#!/usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################################
# Copyright (C) by the DBCSR developers group - All rights reserved                                #
# This file is part of the DBCSR library.                                                          #
#                                                                                                  #
# For information on the license, see the LICENSE file.                                            #
# For further information please visit https://dbcsr.cp2k.org                                      #
# SPDX-License-Identifier: GPL-2.0+                                                                #
####################################################################################################

from __future__ import print_function

import os
from os import path
import re
import argparse

# ===============================================================================
# Helper variables
separator = "//===========================================================================\n"
line_in_string = "{:<70}\\n\\"
variable_declaration = 'std::string {var_name} = "                                     \\n\\'
end_string = '";'
commented_line = r"\s*(//|/\*.*/*/)"
open_comment = r"\s*/\*"
close_comment = r".*\*/"
cusmm_header = (
    "/*------------------------------------------------------------------------------------------------*\n" +
    " * Copyright (C) by the DBCSR developers group - All rights reserved                              *\n" +
    " * This file is part of the DBCSR library.                                                        *\n" +
    " *                                                                                                *\n" +
    " * For information on the license, see the LICENSE file.                                          *\n" +
    " * For further information please visit https://dbcsr.cp2k.org                                    *\n" +
    " * SPDX-License-Identifier: GPL-2.0+                                                              *\n" +
    " *------------------------------------------------------------------------------------------------*/\n" + "\n" +
    "/*****************************************************************************\n" +
    " *  FILE GENERATED BY SCRIPT 'generate_kernels.py' DO NOT EDIT             *\n" +
    " *****************************************************************************/\n" + "\n" + "#ifndef CUSMM_H\n" +
    "#define CUSMM_H\n" + "#include <string>\n")


# ===============================================================================
def main(kernels_folder):
    """
    Find files corresponding to CUDA kernels and write them as strings into a
    C++ header file to be read for JIT-ing
    """
    # Find all files containing "cusmm" kernels in the "kernel" subfolder
    kernels_folder_files = os.listdir(kernels_folder)
    kernel_files = list()
    for f in kernels_folder_files:
        if f[:6] == "cusmm_" and f[-2:] == ".h":
            kernel_files.append(os.path.join(kernels_folder, f))
    print("Found {} kernel files:".format(len(kernel_files)))
    print(*("<- {}".format(kf) for kf in kernel_files), sep="\n")

    # Read
    kernels_h = dict()  # key: path to kernel file (string), value: file content (list of string)
    for kernel_file in kernel_files:
        with open(kernel_file) as f:
            kernels_h[kernel_file] = f.read().splitlines()

    # Construct file containing the kernels as strings
    print("Re-write kernels as strings...")
    file_h = cusmm_header
    for kernel_file, kernel in kernels_h.items():
        kernel_name, _ = path.splitext(path.basename(kernel_file))  # use the filename as name for the kernel
        file_h += "\n" + separator + cpp_function_to_string(kernel, kernel_name) + "\n"
    file_h += "#endif\n"
    file_h += "//EOF"

    # Write
    file_h_path = "cusmm_kernels.h"
    with open(file_h_path, "w") as f:
        f.write(file_h)
    print("Wrote kernel string to file\n-> {}".format(file_h_path))


# ===============================================================================
def cpp_function_to_string(cpp_file, kernel_name):
    """
    Transform a C++ function into a char array
    :param cpp_file: file content
                    (list of strings, each element is a line in the original file)
    :param kernel_name: name of the kernel (string, must be usable as a C++ variable name)
    :return: string containing the kernel written as a C++ char array
    """
    assert re.match(r"^[a-zA-Z]\w*", kernel_name), "kernel_name must be a valid C/C++ variable name"

    out = variable_declaration.format(var_name=kernel_name) + "\n"
    in_comment = False
    for l in cpp_file:
        if not in_comment:
            # ignore comments and empty lines
            if re.match(commented_line, l) is not None or len(l) == 0 or '#include "cusmm_common.h"' in l:
                pass
            elif re.match(open_comment, l) is not None:
                in_comment = True
            else:
                out += line_in_string.format(l.replace('"', '\\"')) + "\n"
        else:  # in_comment == True
            if re.match(close_comment, l) is not None:
                in_comment = False
            else:
                pass

    return out + end_string


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pack CUDA kernels for JIT'ing")
    parser.add_argument(
        "kernels_folder",
        metavar="KERNELS_FOLDER",
        type=str,
        nargs="?",
        default="./kernels",
        help="directory with the kernel header files. Default: %(default)s",
    )

    args = parser.parse_args()
    main(args.kernels_folder)
