#!#/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, datetime
######################################################################################
# Copyright 2020 - Remisson dos Santos Silva (remisson-silva@bol.com.br)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
######################################################################################
#
#
# Input format - 00000000: 4448 4653 342e 3100 0000 0000 0000 0000  DHFS4.1.........
#
#
# TENTAR CRIAR ARQUIVO FORMATO BINARIO
# Renomear o arquivo de quadros gerado pelo timestamp
# separar também pelo canal (câmera)
# pegar o fim do arquivo dav + 4 bytes equivalentes ao tamanho do quadro usados no codec
#
if sys.argv and len(sys.argv) > 0:
	options = {
		'input_file_name':str(sys.argv[1]),
		'output_folder':str(sys.argv[2]),
	}
	print('==================================')
	print('== Starting DHAV Carving Script ==')
	print('==================================')
	print('[%s] .Carving file %s' % (datetime.datetime.now(),options['input_file_name']))

	f__content__ = None
	print('[%s] ...Reading input file' % datetime.datetime.now())
	with open(options['input_file_name'],'r+') as file:
		f__content__ = file.read()
		file.close()
	dvr_code = None
	num_recovered_frames = 0
	print('[%s] ...Processing input file' % datetime.datetime.now())
	if f__content__:

		current_frames_file = ""
		compiled_frames_file = ""

		current_file_frames = ""
		current_file_code = None
		current_file_bytes = None
		current_file_str = None

		HEADER_BYTE = '44484156'
		END_BYTE = '64686176'

		file_in_progress = False
		frame_file_count = 1
		for current_line in f__content__.split('\n'):
			if current_line:
				array = current_line.split(' ')
				if array and len(array) > 0:
					current_file_code = str(array.pop(0)).replace(':','').replace(' ','')
					current_file_str = str(array.pop())
					current_file_bytes = " ".join(array)
					bytes_no_space = "".join(array)
					add_frame = False
					append_file = False
					if HEADER_BYTE in bytes_no_space:
						file_in_progress = True
						add_frame = True
					elif END_BYTE in bytes_no_space:
						if file_in_progress:
							file_in_progress = False
							add_frame = True
							append_file = True
						else:
							current_file_frames = ""

					elif file_in_progress:
						add_frame = True

					if add_frame:
						current_file_frames += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))

					if append_file:
						current_frames_file  += str("%s\n" % current_file_frames)
						compiled_frames_file += str("%s\n" % current_file_frames)
						if current_frames_file:
							ff_name = 'frame%s.DAT' % frame_file_count
							print('[%s] ...Saving %s' % (datetime.datetime.now(),ff_name))
							num_recovered_frames += 1
							with open(options['output_folder'] + ff_name,'w+') as file:
								file.write(current_frames_file)
								file.close()
							frame_file_count += 1
						current_file_frames = ""
						current_frames_file = ""

		if compiled_frames_file:
			print('[%s] ...Saving compiled_frames.txt' % datetime.datetime.now())
			with open(options['output_folder'] + 'compiled_frames.DAT','w+') as file:
				file.write(compiled_frames_file)
				file.close()

	print('[%s] ...Writing output files on %s' % (datetime.datetime.now(), options['output_folder']))
	with open(options['output_folder'] + 'result.txt','w+') as file:
		result_content = "|Num Frames|DVR|\n"
		result_content += "|%s|%s|\n" % (dvr_code,num_recovered_frames)
		file.write(result_content)
		file.close()
	print('[%s] .Finished' % datetime.datetime.now())
