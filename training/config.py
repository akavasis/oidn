## Copyright 2018-2020 Intel Corporation
## SPDX-License-Identifier: Apache-2.0

import os
import sys
import argparse
import time
import torch

from util import *

# Parses the config from the command line arguments
def parse_args(cmd=None, description=None):
  def get_default_device():
    return 'cuda' if torch.cuda.is_available() else 'cpu'

  def get_default_result():
    return '%x' % int(time.time())

  if cmd is None:
    cmd, _ = os.path.splitext(os.path.basename(sys.argv[0]))

  parser = argparse.ArgumentParser(description=description)
  parser.usage = '\rIntel(R) Open Image Denoise - Training\n' + parser.format_usage()

  if cmd in {'preprocess', 'train', 'find_lr'}:
    parser.add_argument('features', type=str, nargs='*', choices=['hdr', 'ldr', 'albedo', 'alb', 'normal', 'nrm', []], help='set of input features')
    parser.add_argument('--transfer', '-x', choices=['srgb', 'pu', 'log'], default=None, help='transfer function')
    parser.add_argument('--preproc_dir', '-P', type=str, default='preproc', help='directory of preprocessed datasets')
    parser.add_argument('--train_data', '-t', type=str, default='train', help='name of the training dataset')

  if cmd in {'preprocess', 'train'}:
    parser.add_argument('--valid_data', '-v', type=str, default='valid', help='name of the validation dataset')

  if cmd in {'preprocess', 'infer'}:
    parser.add_argument('--data_dir', '-D', type=str, default='data', help='directory of datasets (e.g. training, validation, test)')

  if cmd in {'preprocess'}:
    parser.add_argument('--clean', action='store_true', help='delete existing preprocessed datasets')

  if cmd in {'train', 'find_lr', 'infer', 'export', 'visualize'}:
    parser.add_argument('--results_dir', '-R', type=str, default='results', help='directory of training results')
    parser.add_argument('--result', '-r', type=str, default=get_default_result(), help='name of the result to save/load')

  if cmd in {'train', 'infer', 'export'}:
    parser.add_argument('--checkpoint', '-c', type=int, default=0, help='result checkpoint to restore')

  if cmd in {'train', 'find_lr'}:
    parser.add_argument('--batch_size', '--bs', type=int, default=8, help='size of the mini-batches')
    parser.add_argument('--tile_size', '--ts', type=int, default=256, help='size of the cropped image tiles')
    parser.add_argument('--loss', '-l', type=str, choices=['l1', 'mape', 'smape', 'l2', 'ssim', 'msssim', 'l1_msssim', 'l1_grad'], default='l1_msssim', help='loss function')
    parser.add_argument('--seed', '-s', type=int, default=42, help='seed for random number generation')
    parser.add_argument('--loaders', type=int, default=4, help='number of data loader threads')

  if cmd in {'train'}:
    parser.add_argument('--epochs', '-e', type=int, default=2100, help='number of training epochs')
    parser.add_argument('--lr', '--learning_rate', type=float, default=2e-6, help='minimum learning rate')
    parser.add_argument('--max_lr', '--max_learning_rate', type=float, default=2e-4, help='maximum learning rate')
    parser.add_argument('--lr_cycle_epochs', type=int, default=250, help='number of training epochs per learning rate cycle')
    parser.add_argument('--valid_epochs', type=int, default=10, help='validate every this many epochs')
    parser.add_argument('--save_epochs', type=int, default=10, help='save checkpoints every this many epochs')
    parser.add_argument('--log_steps', type=int, default=100, help='save summaries every this many steps')

  if cmd in {'infer', 'compare_exr'}:
    parser.add_argument('--metric', '-m', type=str, nargs='*', choices=['mse', 'ssim'], default=['ssim'], help='metrics to compute')

  if cmd in {'infer'}:
    parser.add_argument('--input_data', '-i', type=str, default='test', help='name of the input dataset')
    parser.add_argument('--output_dir', '-O', type=str, default='infer', help='directory of output images')
    parser.add_argument('--format', '-f', type=str, nargs='*', choices=['exr', 'pfm', 'png'], default=['png'], help='output image formats')

  if cmd in {'compare_exr'}:
    parser.add_argument('input', type=str, nargs=2, help='input images')

  if cmd in {'convert_exr', 'split_exr'}:
    parser.add_argument('input', type=str, help='input image')

  if cmd in {'convert_exr'}:
    parser.add_argument('output', type=str, help='output image')

  if cmd in {'compare_exr', 'convert_exr'}:
    parser.add_argument('--exposure', '-ev', type=float, default=1., help='exposure value for HDR image')

  if cmd in {'preprocess', 'train', 'find_lr', 'infer', 'export'}:
    parser.add_argument('--device', '-d', type=str, choices=['cpu', 'cuda'], default=get_default_device(), help='device to use')
    parser.add_argument('--deterministic', '--det', action='store_true', help='makes computations deterministic (slower performance)')

  cfg = parser.parse_args()

  if cmd in {'preprocess', 'train', 'find_lr'}:
    # Replace full feature names with abbreviations
    FEATURE_ABBREV = {'albedo' : 'alb', 'normal' : 'nrm'}
    cfg.features = [FEATURE_ABBREV.get(f, f) for f in cfg.features]
    # Remove duplicate features
    cfg.features = list(dict.fromkeys(cfg.features).keys())

    # Check features
    if ('ldr' in cfg.features) == ('hdr' in cfg.features):
      error('either hdr or ldr must be specified as input feature')

    # Set the transfer function if undefined
    if not cfg.transfer:
      cfg.transfer = 'pu' if 'hdr' in cfg.features else 'srgb'

  return cfg

# Loads the config from a directory
def load_config(dir):
  filename = os.path.join(dir, 'config.json')
  cfg = load_json(filename)
  return argparse.Namespace(**cfg)

# Saves the config to a directory
def save_config(dir, cfg):
  filename = os.path.join(dir, 'config.json')
  save_json(filename, vars(cfg))