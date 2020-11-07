from PIL import Image, ImageDraw, ImageFont

def generatePic(basePic, title, generatedPic, num, coin):
	title_font = ImageFont.truetype("../pics/Deng.ttf", size=58)
	info_font = ImageFont.truetype("../pics/simfang.ttf", size=30)
	img = Image.open(basePic)
	bg_size = img.size
	# print(img)
	img2 = Image.open("../pics/bg.png")
	# print(img2)

	# image = Image.open("../pics/empty.png")
	# print(image)
	# image = img.alpha_composite(image, img)
	# image = img.alpha_composite(image, img2)
	# image = Image.blend(img, img2, 0.5)
	# image = Image.composite(img, img2, img2)
	img.paste(img2, (0, 0), img2)
	image = img
	img = Image.open(basePic)
	image = Image.blend(img, image, 0.7)
	draw = ImageDraw.Draw(image)

	colort="#ffffff"
	color = "#333333"
	info1 = "题目数量：" + str(num) + "    悬赏金额：" + str(coin)

	title_size = title_font.getsize(title)
	title_coordinate = int((bg_size[0] - title_size[0]) / 2), int((bg_size[1] - title_size[1]) / 2) -35
	draw.text(title_coordinate, u'%s' % title, colort, title_font)

	info_size = info_font.getsize(info1)
	info_coordinate = int((bg_size[0] - info_size[0]) / 2), int((bg_size[1] - info_size[1]) / 2) + 36
	draw.text(info_coordinate, u'%s' % info1, color, info_font)

	# info_size = info_font.getsize(info2)
	# info_coordinate = int((bg_size[0] - info_size[0]) / 2), int((bg_size[1] - info_size[1]) / 2) + 80
	# draw.text(info_coordinate, u'%s' % info2, color, info_font)
	image.save(generatedPic)

# test only
# for i in range(1, 8):
# 	generatePic("../pics/"+str(i)+".jpg",
# 				"选择题1号测试", "../pics/"+str(i)+"-1.png",
# 				5, 10)
