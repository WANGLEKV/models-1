# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""YoloV5 train."""
import os
import time
import mindspore as ms
import mindspore.nn as nn
import mindspore.communication as comm

from src.yolo import YOLOV5, YoloWithLossCell
from src.logger import get_logger
from src.util import AverageMeter, get_param_groups, cpu_affinity
from src.lr_scheduler import get_lr
from src.yolo_dataset import create_yolo_dataset
from src.initializer import default_recurisive_init, load_yolov5_params

from model_utils.config import config
from model_utils.device_adapter import get_device_id

# only useful for huawei cloud modelarts.
from model_utils.moxing_adapter import moxing_wrapper, modelarts_pre_process, modelarts_post_process


ms.set_seed(1)


def init_distribute():
    comm.init()
    config.rank = comm.get_rank()
    config.group_size = comm.get_group_size()
    ms.set_auto_parallel_context(parallel_mode=ms.ParallelMode.DATA_PARALLEL, gradients_mean=True,
                                 device_num=config.group_size)


def train_preprocess():
    if config.lr_scheduler == 'cosine_annealing' and config.max_epoch > config.T_max:
        config.T_max = config.max_epoch

    config.lr_epochs = list(map(int, config.lr_epochs.split(',')))
    config.data_root = os.path.join(config.data_dir, 'train2017')
    config.annFile = os.path.join(config.data_dir, 'annotations/instances_train2017.json')
    device_id = get_device_id()
    ms.set_context(mode=ms.GRAPH_MODE, device_target=config.device_target, device_id=device_id)

    if config.is_distributed:
        # init distributed
        init_distribute()

    # for promoting performance in GPU device
    if config.device_target == "GPU" and config.bind_cpu:
        cpu_affinity(config.rank, min(config.group_size, config.device_num))

    # logger module is managed by config, it is used in other function. e.x. config.logger.info("xxx")
    config.logger = get_logger(config.output_dir, config.rank)
    config.logger.save_args(config)


@moxing_wrapper(pre_process=modelarts_pre_process, post_process=modelarts_post_process, pre_args=[config])
def run_train():
    train_preprocess()

    loss_meter = AverageMeter('loss')
    dict_version = {'yolov5s': 0, 'yolov5m': 1, 'yolov5l': 2, 'yolov5x': 3}
    network = YOLOV5(is_training=True, version=dict_version[config.yolov5_version])
    # default is kaiming-normal
    default_recurisive_init(network)
    load_yolov5_params(config, network)
    network = YoloWithLossCell(network)

    ds = create_yolo_dataset(image_dir=config.data_root, anno_path=config.annFile, is_training=True,
                             batch_size=config.per_batch_size, device_num=config.group_size,
                             rank=config.rank, config=config)
    config.logger.info('Finish loading dataset')

    steps_per_epoch = ds.get_dataset_size()
    lr = get_lr(config, steps_per_epoch)
    opt = nn.Momentum(params=get_param_groups(network), momentum=config.momentum, learning_rate=ms.Tensor(lr),
                      weight_decay=config.weight_decay, loss_scale=config.loss_scale)
    network = nn.TrainOneStepCell(network, opt, config.loss_scale // 2)
    network.set_train()

    data_loader = ds.create_dict_iterator()
    first_step = True
    t_end = time.time()

    for epoch_idx in range(config.max_epoch):
        for step_idx, data in enumerate(data_loader):
            images = data["image"]
            input_shape = images.shape[2:4]
            input_shape = ms.Tensor(tuple(input_shape[::-1]), ms.float32)
            loss = network(images, data['bbox1'], data['bbox2'], data['bbox3'], data['gt_box1'], data['gt_box2'],
                           data['gt_box2'], input_shape)
            loss_meter.update(loss.asnumpy())

            # it is used for loss, performance output per config.log_interval steps.
            if (epoch_idx * steps_per_epoch + step_idx) % config.log_interval == 0:
                time_used = time.time() - t_end
                if first_step:
                    fps = config.per_batch_size * config.group_size / time_used
                    per_step_time = time_used * 1000
                    first_step = False
                else:
                    fps = config.per_batch_size * config.log_interval * config.group_size / time_used
                    per_step_time = time_used / config.log_interval * 1000
                config.logger.info('epoch[{}], iter[{}], {}, fps:{:.2f} imgs/sec, '
                                   'lr:{}, per step time: {}ms'.format(epoch_idx + 1, step_idx + 1,
                                                                       loss_meter, fps, lr[step_idx], per_step_time))
                t_end = time.time()
                loss_meter.reset()
        if config.rank == 0:
            ckpt_name = os.path.join(config.output_dir, "yolov5_{}_{}.ckpt".format(epoch_idx + 1, steps_per_epoch))
            ms.save_checkpoint(network, ckpt_name)

    config.logger.info('==========end training===============')


if __name__ == "__main__":
    run_train()
