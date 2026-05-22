# Copyright 2023 Google LLC. All rights reserved.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# Copy the pssh-box.py script and its protos into the required directory
# structure.
set(PSSH_BOX_OUTPUTS
    ${CMAKE_BINARY_DIR}/packager/pssh-box.py
    ${CMAKE_BINARY_DIR}/packager/pssh-box-protos
    ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/widevine_common_encryption_pb2.py
    ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/widevine_pssh_data_pb2.py)

if(NOT USE_SYSTEM_DEPENDENCIES)
  # When bundling the protobuf python runtime, ensure the generated
  # python_edition_defaults.py (produced by packager/third_party/protobuf)
  # makes it into pssh-box-protos.  Tracking it as both an OUTPUT and a
  # file-level dependency ensures incremental builds re-copy the runtime
  # when protobuf_py regenerates the file (e.g. after a protobuf upgrade).
  set(PSSH_BOX_EDITION_DEFAULTS_SRC
      ${CMAKE_BINARY_DIR}/packager/third_party/protobuf/py/google/protobuf/internal/python_edition_defaults.py)
  set(PSSH_BOX_EDITION_DEFAULTS_DST
      ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/google/protobuf/internal/python_edition_defaults.py)
  list(APPEND PSSH_BOX_OUTPUTS ${PSSH_BOX_EDITION_DEFAULTS_DST})
  set(PROTO_COPY_EXTRA_DEPENDS ${PSSH_BOX_EDITION_DEFAULTS_SRC})
  set(PROTO_COPY_EXTRAS
      COMMAND
          ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_BINARY_DIR}/packager/third_party/protobuf/py/google
          ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/google)
endif()

add_custom_command(
    DEPENDS
        protobuf_py
        widevine_protos
        pssh-box.py
        ${PROTO_COPY_EXTRA_DEPENDS}
    OUTPUT ${PSSH_BOX_OUTPUTS}
    COMMAND
        ${CMAKE_COMMAND} -E make_directory
        ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/
    COMMAND
        ${CMAKE_COMMAND} -E copy
        ${CMAKE_BINARY_DIR}/packager/media/base/widevine_common_encryption_pb2.py
        ${CMAKE_BINARY_DIR}/packager/media/base/widevine_pssh_data_pb2.py
        ${CMAKE_BINARY_DIR}/packager/pssh-box-protos/
    COMMAND
        ${CMAKE_COMMAND} -E copy
        ${CMAKE_CURRENT_SOURCE_DIR}/pssh-box.py
        ${CMAKE_BINARY_DIR}/packager
    ${PROTO_COPY_EXTRAS})

add_custom_target(pssh_box_py ALL DEPENDS ${PSSH_BOX_OUTPUTS})

# Always install the python tools.
install(PROGRAMS ${CMAKE_BINARY_DIR}/packager/pssh-box.py
        DESTINATION ${CMAKE_INSTALL_BINDIR})
install(DIRECTORY ${CMAKE_BINARY_DIR}/packager/pssh-box-protos
        DESTINATION ${CMAKE_INSTALL_BINDIR})

# Smoke test: ensure the bundled python protobuf runtime can actually be
# imported by pssh-box.py.  This catches build regressions like the missing
# google/protobuf/internal/python_edition_defaults.py generation step (which
# broke pssh-box.py with an ImportError when the bundled protobuf runtime
# was upgraded past v6/33.x).
if(NOT SKIP_INTEGRATION_TESTS)
  add_test(
    NAME pssh_box_py_smoke_test
    COMMAND
      "${Python3_EXECUTABLE}" "${CMAKE_BINARY_DIR}/packager/pssh-box.py"
      --widevine-system-id
      --key-id 11223344556677889900AABBCCDDEEFF
      --content-id 1234
      --provider test
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/packager)
endif()
