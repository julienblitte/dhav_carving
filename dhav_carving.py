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
# - Corrigir erros do header
# - Implementar a captura do footer
# - Implementar as regras de salvar por canal
# - Implementar a regra pra permitir apenas quadros principais
# - Salvar formato binário
# - Teste com ffplay
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

		current_temp_frame_buffer = ""
		current_frames_file = ""
		compiled_frames_file = ""

		current_file_frames = ""
		current_file_code = None
		current_file_bytes = None
		current_file_str = None
		current_padding = 0

		HEADER_BYTE = '44484156'
		END_BYTE = '64686176'
		TYPE_AUDIO = 'f1'
		TYPE_MAIN = 'fd'
		TYPE_COMPL = 'fc'

		h_pos = None
		file_in_progress = False
		check_dhav_header = False
		process_incomplete_header = False

		frame_params = {
			'current_byte_header':'',
			'current_byte_frame_type':'',
			'current_byte_channel':'',
			'current_byte_id_seq':'',
			'current_byte_size':'',
			'current_byte_time':'',
			'current_byte_time_sec':'',
		}

		for current_line in f__content__.split('\n'):
			if current_line:
				array = current_line.split(' ')
				if array and len(array) > 0:
					current_file_code = str(array.pop(0)).replace(' ','')
					# current_file_code = str(array.pop(0)).replace(':','').replace(' ','')
					current_file_str = str(array.pop())
					current_file_bytes = " ".join(array)
					bytes_no_space = "".join(array)

					add_frame = False
					append_file = False

					pending_to_extract = {}
					incomplete_pending_to_extract = {}

					if pending_to_extract or incomplete_pending_to_extract:
						for key in [
							'current_byte_header',
							'current_byte_frame_type',
							'current_byte_channel',
							'current_byte_id_seq',
							'current_byte_size',
							'current_byte_time',
							'current_byte_time_sec',]:

							if key in incomplete_pending_to_extract:
								ind_l = incomplete_pending_to_extract[key]
								frame_params.update({
									key : ind_l[0] + bytes_no_space[0,ind_l[1]],
								})

							elif key in pending_to_extract:
								ind_l = pending_to_extract[key]
								frame_params.update({
									key : bytes_no_space[ind_l[0],ind_l[1]]
								})

						incomplete_pending_to_extract = {}
						pending_to_extract = {}

					if check_dhav_header:
						if frame_params['current_byte_header'] == HEADER_BYTE:
							process_incomplete_header = True
						else:
							current_temp_frame_buffer = ""
						check_dhav_header = False

					if END_BYTE in bytes_no_space:
						#
						#
						# TODO
						# se na mesma linha tive rum fechamento e uma abertura
						# conseguir extrair os dois arquivos
						#
						# os 4 bytes após o dhav no rodapé são referentes ao tamanho do quadro (mesmo 
						# valor do campo tamanho do quadro encontrado no cabeçalho) e são utilizados 
						# pela ferramenta FFPLAY na reprodução dos vídeos,
						#
						if file_in_progress:
							file_in_progress = False
							add_frame = True
							append_file = True
						else:
							current_file_frames = ""

					if process_incomplete_header:
						total = 8
						desc = total - current_padding

						frame_params.update({
							'current_byte_frame_type' :  bytes_no_space[8 - desc, (10 - total) + current_padding],
							'current_byte_channel' : bytes_no_space[12 - desc ,(14 - total) + current_padding ],
							'current_byte_id_seq' : bytes_no_space[16 - desc,(24 - total) + current_padding],
							'current_byte_size' : bytes_no_space[24 - desc,(32 - total) + current_padding],
						})

						last_indx = (32 - total) + current_padding

						if last_indx == 26:
							incomplete_pending_to_extract.update({
								'current_byte_time': [bytes_no_space[26:32], 2],
							})
							pending_to_extract.update({
								'current_byte_time_sec': [2,6],
							})

						elif last_indx == 28:
							incomplete_pending_to_extract.update({
								'current_byte_time': [bytes_no_space[28:32], 4],
							})
							pending_to_extract.update({
								'current_byte_time_sec': [4,8],
							})

						elif last_indx == 30:
							incomplete_pending_to_extract.update({
								'current_byte_time': [bytes_no_space[30:32], 6],
							})
							pending_to_extract.update({
								'current_byte_time_sec': [6,10],
							})

						current_file_frames += current_temp_frame_buffer

						file_in_progress = True
						process_incomplete_header = False

					elif HEADER_BYTE in bytes_no_space:
						file_in_progress = True
						add_frame = True

						try:
							h_pos = bytes_no_space.index(HEADER_BYTE)
							if h_pos == 0:
								frame_params.update({
									'current_byte_header':bytes_no_space[0:8],
									'current_byte_frame_type':bytes_no_space[8:10],
									'current_byte_channel':bytes_no_space[12:14],
									'current_byte_id_seq':bytes_no_space[16:24],
									'current_byte_size':bytes_no_space[24:32],
								})

								pending_to_extract.update({
									'current_byte_time':[0,8],
									'current_byte_time_sec':[8,12],
								})

							else:
								c_padding = 0
								for c in [ ['current_byte_header',0 + h_pos,8 + h_pos],
									['current_byte_frame_type',8 + h_pos,10 + h_pos],
									['current_byte_channel',12 + h_pos,14 + h_pos],
									['current_byte_id_seq',16 + h_pos,24 + h_pos],
									['current_byte_size',24 + h_pos,32 + h_pos] ]:

									if bytes_no_space[c[1],c[2]]:
										frame_params.update({c[0] : bytes_no_space[c[1],c[2]]})
									elif bytes_no_space[c[1],c[32]]:
										added_v = bytes_no_space[c[1],c[32]]
										diff_v = c[2] - c[1]
										pend_v = diff_v - len(added_v)
										incomplete_pending_to_extract.update({
											c[0] : [added_v, pend_v]
										})
										c_padding += pend_v
									else:
										pending_to_extract.update({ c[0] : [c_padding, c[2] - c[1]], })
										c_padding += c[2] - c[1]

								pending_to_extract.update({
									'current_byte_time',[0 + c_padding,8 + c_padding],
									'current_byte_time_sec',[8 + c_padding,12 + c_padding],
								})

						except ValueError as e:
							print('Cannot extract the header params for: '+str(current_line))

					elif '44' == bytes_no_space[30:32]:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['44', 6]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0000 0044',current_file_str))
						current_padding = 6

					elif '4448' == bytes_no_space[28:32]:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['4448', 4]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0000 4448',current_file_str))
						current_padding = 4

					elif '444841' == bytes_no_space[26:32]:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['444841', 2]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0044 4841',current_file_str))
						current_padding = 2

					elif file_in_progress:
						add_frame = True

					if add_frame:
						current_file_frames += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))

					if append_file:
						current_frames_file  += str("%s\n" % current_file_frames)
						compiled_frames_file += str("%s\n" % current_file_frames)
						if current_frames_file:

							ff_name = 'frame%s.%s%s.DAT' % (
								int(frame_params['current_byte_id_seq'], 16),
								int(frame_params['current_byte_time'], 16),
								int(frame_params['current_byte_time_sec'], 16)
							)
							print('[%s] ...Saving %s ID:%s Type:%s Size:%s' % (
								datetime.datetime.now(),
								ff_name,
								int(frame_params['current_byte_id_seq'], 16),
								frame_params['current_byte_frame_type'],
								int(frame_params['current_byte_size'], 16),
							))
							num_recovered_frames += 1
							# with open(options['output_folder'] + ff_name,'wb') as file:
							with open(options['output_folder'] + ff_name,'w+') as file:
								file.write(current_frames_file)
								file.close()

						current_file_frames = ''
						current_frames_file = ''
						current_temp_frame_buffer = ''
						current_padding = 0
						h_pos = None
						frame_params = {
							'current_byte_header':'',
							'current_byte_frame_type':'',
							'current_byte_channel':'',
							'current_byte_id_seq':'',
							'current_byte_size':'',
							'current_byte_time':'',
							'current_byte_time_sec':'',
						}

		if compiled_frames_file:
			print('[%s] ...Saving compiled_frames.txt' % datetime.datetime.now())
			# with open(options['output_folder'] + 'compiled_frames.DAT','wb') as file:
			with open(options['output_folder'] + 'compiled_frames.DAT','w+') as file:
				file.write(compiled_frames_file)
				file.close()

	print('[%s] ...Writing output files on %s' % (datetime.datetime.now(), options['output_folder']))
	with open(options['output_folder'] + 'result.txt','w+') as file:
		result_content = "|DVR|Num Frames|\n"
		result_content += "|%s|%s|\n" % (dvr_code,num_recovered_frames)
		file.write(result_content)
		file.close()
	print('[%s] .Finished' % datetime.datetime.now())
