from PIL import Image, ImageDraw, ImageFont
import os


def generate_pic(base_pic_dir, base_pic_name, title, num, coin, ddl):
	title_font = ImageFont.truetype(os.path.join('pics', 'Deng.ttf'), size=55)
	info_font = ImageFont.truetype(os.path.join('pics', 'simfang.ttf'), size=30)
	img_ = Image.open(os.path.join(base_pic_dir, base_pic_name))

	img2 = Image.open(os.path.join('pics', 'bg.png'))
	bg_size = img2.size

	img = img_.resize(bg_size)

	img.paste(img2, (0, 0), img2)
	image = img
	img = Image.open(os.path.join(base_pic_dir, base_pic_name)).resize(bg_size)
	image = Image.blend(img, image, 0.7)
	draw = ImageDraw.Draw(image)

	colort = "#ffffff"
	color = "#333333"
	info1 = "题数：" + str(num) + "  赏金：" + str(coin) + "  截止：" + str(ddl)

	title_size = title_font.getsize(title)
	title_coordinate = int((bg_size[0] - title_size[0]) / 2), int((bg_size[1] - title_size[1]) / 2) - 35
	draw.text(title_coordinate, u'%s' % title, colort, title_font)

	info_size = info_font.getsize(info1)
	info_coordinate = int((bg_size[0] - info_size[0]) / 2), int((bg_size[1] - info_size[1]) / 2) + 36
	draw.text(info_coordinate, u'%s' % info1, color, info_font)

	image.save(os.path.join('image', '_mission_bg', title + '.png'))
