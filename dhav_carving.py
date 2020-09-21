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
		TYPE_MAIN = 'fd'

		h_pos = None
		file_in_progress = False
		check_dhav_header = False
		process_incomplete_header = False
		blockc_find_h = False
		insert_when_find_type = False
		searching_incomplete_end = False
		created_channel_folders = []

		frame_params = {
			'current_byte_header':'',
			'current_byte_frame_type':'',
			'current_byte_channel':'',
			'current_byte_id_seq':'',
			'current_byte_size':'',
			'current_byte_time':'',
			'current_byte_time_sec':'',
			'current_byte_end':'',
		}

		pending_to_extract = {}
		incomplete_pending_to_extract = {}

		for current_line in f__content__.split('\n'):
			if current_line:
				array = current_line.split(' ')
				if array and len(array) > 0:
					current_file_code = str(array.pop(0)).replace(' ','')
					current_file_str = str(array.pop())
					current_file_bytes = " ".join(array)
					bytes_no_space = "".join(array)[0:32]

					try:
						if not file_in_progress and int(bytes_no_space) <= 0:
							continue
					except:
						pass

					add_frame = False

					if pending_to_extract or incomplete_pending_to_extract:
						for key in [
							'current_byte_header',
							'current_byte_frame_type',
							'current_byte_channel',
							'current_byte_id_seq',
							'current_byte_size',
							'current_byte_time',
							'current_byte_time_sec',
							'current_byte_end',]:

							if key in incomplete_pending_to_extract:
								ind_l = incomplete_pending_to_extract[key]
								frame_params.update({
									key : ind_l[0] + bytes_no_space[0:ind_l[1]],
								})

							elif key in pending_to_extract:
								ind_l = pending_to_extract[key]
								frame_params.update({
									key : bytes_no_space[ind_l[0]:ind_l[1]]
								})

						incomplete_pending_to_extract = {}
						pending_to_extract = {}

					if check_dhav_header:
						if frame_params['current_byte_header'] == HEADER_BYTE:
							process_incomplete_header = True
						else:
							current_temp_frame_buffer = ""
						check_dhav_header = False

					find_end_incomplete = False
					if searching_incomplete_end:
						if frame_params['current_byte_end'] == END_BYTE:
							find_end_incomplete = True
						else:
							frame_params.update({'current_byte_end':''})
						searching_incomplete_end = False

					if END_BYTE in bytes_no_space or find_end_incomplete:
						if file_in_progress:
							if frame_params['current_byte_frame_type'] == TYPE_MAIN:
								if insert_when_find_type:
									current_file_frames += current_temp_frame_buffer
									insert_when_find_type = False
								current_file_frames += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))

							current_frames_file  += str("%s\n" % current_file_frames)
							compiled_frames_file += str("%s\n" % current_file_frames)
							if current_frames_file:
								_id_seq = int(frame_params['current_byte_id_seq'], 16) if frame_params['current_byte_id_seq'] else ''
								_time = int(frame_params['current_byte_time'], 16) if frame_params['current_byte_time'] else ''
								_time_sec = int(frame_params['current_byte_time_sec'], 16) if frame_params['current_byte_time_sec'] else ''
								_size = int(frame_params['current_byte_size'], 16) if frame_params['current_byte_size'] else ''

								if _size:
									save_path = None
									_channel = frame_params['current_byte_channel']
									if not _channel in created_channel_folders:
										try:
											save_path = "%s/channel_%s/" % (options['output_folder'],_channel)
											os.makedirs(save_path)
											created_channel_folders.append(_channel)
										except:
											pass
									else:
										save_path = "%s/channel_%s/" % (options['output_folder'],_channel)

									int_timestamp = int(frame_params['current_byte_time'],16)
									if int_timestamp and len(str(int_timestamp)) < 9:
										while len(str(int_timestamp)) < 9:
											stmp = "%s0" % int_timestamp
											int_timestamp = int(stmp)
									elif int_timestamp and len(str(int_timestamp)) > 9:
										int_timestamp = int(str(int_timestamp)[0:9])

									d = datetime.datetime.fromtimestamp(int_timestamp)

									ff_name = 'frame%s.%s.h264' % (
										d.strftime("%Y_%m_%d_%H_%M_%S"),
										_id_seq,
									)
									print('[%s] ...Saving %s ID:%s Type:%s Size:%s' % (
										datetime.datetime.now(),
										ff_name,
										_id_seq,
										frame_params['current_byte_frame_type'],
										_size,
									))
									num_recovered_frames += 1

									if not save_path:
										save_path = options['output_folder'] + '/'
									with open(save_path + ff_name,'w+b') as file:
										file.write(current_frames_file.encode('ascii'))
										file.close()

						blockc_find_h = False
						current_file_frames = ''
						current_frames_file = ''
						current_temp_frame_buffer = ''
						current_padding = 0
						insert_when_find_type = False
						h_pos = None
						frame_params = {
							'current_byte_header':'',
							'current_byte_frame_type':'',
							'current_byte_channel':'',
							'current_byte_id_seq':'',
							'current_byte_size':'',
							'current_byte_time':'',
							'current_byte_time_sec':'',
							'current_byte_end':'',
						}

					elif '646861' == bytes_no_space[26:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_end' : ['646861', 2]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))
						current_padding = 2
						searching_incomplete_end = True

					elif '6468' == bytes_no_space[28:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_end' : ['6468', 4]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))
						current_padding = 4
						searching_incomplete_end = True

					elif '64' == bytes_no_space[30:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_end' : ['64', 6]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))
						current_padding = 6
						searching_incomplete_end = True

					if process_incomplete_header:
						total = 8
						desc = total - current_padding

						frame_params.update({
							'current_byte_frame_type' :  bytes_no_space[8 - desc : (10 - total) + current_padding],
							'current_byte_channel' : bytes_no_space[12 - desc  :(14 - total) + current_padding ],
							'current_byte_id_seq' : bytes_no_space[16 - desc :(24 - total) + current_padding],
							'current_byte_size' : bytes_no_space[24 - desc :(32 - total) + current_padding],
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

						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))
						insert_when_find_type = True

						file_in_progress = True
						process_incomplete_header = False

					elif HEADER_BYTE in bytes_no_space:
						file_in_progress = True
						add_frame = True
						blockc_find_h = True
						searching_incomplete_end = False

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

									if bytes_no_space[c[1]:c[2]]:
										frame_params.update({c[0] : bytes_no_space[c[1]:c[2]]})
									elif bytes_no_space[c[1]:32]:
										added_v = bytes_no_space[c[1]:32]
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
									'current_byte_time':[0 + c_padding,8 + c_padding],
									'current_byte_time_sec':[8 + c_padding,12 + c_padding],
								})

						except ValueError as e:
							print('Cannot extract the header params for: '+str(current_line))

					elif '444841' == bytes_no_space[26:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['444841', 2]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0044 4841',current_file_str))
						current_padding = 2

					elif '4448' == bytes_no_space[28:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['4448', 4]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0000 4448',current_file_str))
						current_padding = 4

					elif '44' == bytes_no_space[30:32] and not blockc_find_h and not file_in_progress:
						check_dhav_header = True
						incomplete_pending_to_extract.update({
							'current_byte_header' : ['44', 6]
						})
						current_temp_frame_buffer += str('%s\t%s\t%s\n' % (
							current_file_code,'0000 0000 0000 0000 0000 0000 0000 0044',current_file_str))
						current_padding = 6

					elif file_in_progress:
						add_frame = True

					if add_frame:

						if frame_params['current_byte_frame_type'] == TYPE_MAIN:
							if insert_when_find_type:
								current_file_frames += current_temp_frame_buffer
								insert_when_find_type = False
							current_file_frames += str('%s\t%s\t%s\n' % (current_file_code,current_file_bytes,current_file_str))
						else:
							blockc_find_h = False
							current_file_frames = ''
							current_frames_file = ''
							current_temp_frame_buffer = ''
							current_padding = 0
							insert_when_find_type = False
							h_pos = None
							frame_params = {
								'current_byte_header':'',
								'current_byte_frame_type':'',
								'current_byte_channel':'',
								'current_byte_id_seq':'',
								'current_byte_size':'',
								'current_byte_time':'',
								'current_byte_time_sec':'',
								'current_byte_end':'',
							}
							continue

		if compiled_frames_file:
			print('[%s] ...Saving compiled_frames.txt' % datetime.datetime.now())
			with open(options['output_folder'] + '/compiled_frames.h264','wb') as file:
				file.write(compiled_frames_file)
				file.close()

	print('[%s] ...Writing output files on %s' % (datetime.datetime.now(), options['output_folder']))
	with open(options['output_folder'] + '/result.txt','w+') as file:
		result_content = "|DVR|Num Frames|\n"
		result_content += "|%s|%s|\n" % (dvr_code,num_recovered_frames)
		file.write(result_content)
		file.close()
	print('[%s] .Finished' % datetime.datetime.now())
