// Copyright 2009-2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "image.ih"

struct OutputCopy
{
  // Source
  uniform Image src;

  // Destination
  uniform Image dst;

  // Size
  uniform int H;
  uniform int W;
};

export void OutputCopy_kernel(uniform OutputCopy* uniform self, uniform int h)
{
  foreach (w = 0 ... self->W)
  {
    // Load
    vec3f value = get3f(self->src, h, w);

    // Store
    set3f(self->dst, h, w, value);
  }
}