# DHAV Carving Script

DVR - DHAV Carving

1 - Execute the following command:
`
$ dd if=hd502hi.dd bs=4096 skip=0000 2>/dev/null | xxd > result_1.txt
`

Something like that will be generated into the file result_1.txt:
`
00000000: 4448 4653 342e 3100 0000 0000 0000 0000  DHFS4.1.........
`

2 - Import the file by script
`
$ python dhav_carving.py result_1.txt result_1
`

Params:
# Path of input file
# Result folder path
