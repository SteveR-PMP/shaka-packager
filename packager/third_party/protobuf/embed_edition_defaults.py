#!/usr/bin/env python3
# Copyright 2026 Google LLC. All rights reserved.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Embed serialized FeatureSetDefaults into a Python template.

This is a small reimplementation of protobuf's Bazel-only
``//editions:internal_defaults_escape`` tool (see
``packager/third_party/protobuf/source/editions/internal_defaults_escape.cc``).
It takes the binary FeatureSetDefaults blob produced by
``protoc --edition_defaults_out`` and substitutes it into the Python template
``google/protobuf/internal/python_edition_defaults.py.template`` to produce
the runtime module ``python_edition_defaults.py`` that the protobuf Python
runtime imports from descriptor_pool.py.

Only the default ``octal`` encoding (matching ``absl::CEscape``) is needed
for the Python template, so that is all this script supports.
"""

import argparse
import sys


def octal_escape(data):
  """Return ``data`` formatted like absl::CEscape with use_hex=false.

  The result is a string that can be placed inside a Python bytes literal
  (e.g. ``b"<result>"``) and parsed back to the original bytes.
  """
  out = []
  for b in data:
    if b == 0x0A:
      out.append('\\n')
    elif b == 0x0D:
      out.append('\\r')
    elif b == 0x09:
      out.append('\\t')
    elif b == 0x22:
      out.append('\\"')
    elif b == 0x27:
      out.append("\\'")
    elif b == 0x5C:
      out.append('\\\\')
    elif 0x20 <= b < 0x7F:
      out.append(chr(b))
    else:
      # Always emit three octal digits so the escape is unambiguous when
      # followed by another digit.
      out.append('\\%03o' % b)
  return ''.join(out)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--defaults_path', required=True,
                      help='Path to the FeatureSetDefaults .binpb produced '
                           'by `protoc --edition_defaults_out`.')
  parser.add_argument('--template_path', required=True,
                      help='Path to python_edition_defaults.py.template.')
  parser.add_argument('--output_path', required=True,
                      help='Path to write the generated .py file to.')
  parser.add_argument('--placeholder', required=True,
                      help='String in the template to replace with the '
                           'escaped defaults blob.')
  args = parser.parse_args()

  with open(args.defaults_path, 'rb') as f:
    defaults = f.read()

  escaped = octal_escape(defaults)

  with open(args.template_path, 'r') as f:
    content = f.read()

  if args.placeholder not in content:
    sys.stderr.write(
        'Placeholder %r not found in template %s\n'
        % (args.placeholder, args.template_path))
    return 1

  content = content.replace(args.placeholder, escaped)

  with open(args.output_path, 'w') as f:
    f.write(content)

  return 0


if __name__ == '__main__':
  sys.exit(main())
