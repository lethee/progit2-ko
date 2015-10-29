#-*- coding: utf-8 -*-
import re
import os
import shutil
from collections import OrderedDict

figure_dict = {} # 'local.png':'1-1'
index_set = set()

def parse_comment(line):
	global book, block, in_block

	if line.startswith('/////'):
		book.append("<원문>\n")
		book.extend(block)
		book.append("</원문>\n\n")

		block = []
		in_block = ''
	else:
	  block.append(line)

def parse_code(line):
	global book, block, in_block

	if line.startswith('//////////'):
		raise Exception('Comment in Code')

	if in_block == 'code':
		if line.startswith('----'):
			in_block = 'code-line'
			book.append('<코드>\n')
			return
		if line.startswith('  '):
			in_block = 'code-indent'
			book.append('<코드>\n')
			book.append(line)
			return
	if in_block == 'code-line':
		if line.startswith('----'):
			in_block = ''
			book.append('</코드>\n')
			return
		book.append(line)
	if in_block == 'code-indent':
		if line.startswith('  '):
			book.append(line)
			return
		in_block = ''
		book.append('</코드>\n')


parse_image_desc = ''
def parse(line):
	global book, depth, cwd, block, in_block, index_fig_ch, index_fig, parse_image_desc

	# block - comment
	if in_block == 'comment':
		parse_comment(line)
		return

	# block - code
	if in_block.startswith('code'):
		parse_code(line)
		return

	# comment
	if line.startswith('/////'):
		in_block = 'comment'
		return

	# code
	if line.startswith('[source'):
		in_block = 'code'
		return

	# metadata
	if line.startswith(':'):
		return
	
	# include	
	m = re.match(r"include::(.*)\[\]", line)
	if m:
		path = cwd + "/" + m.group(1)
		old_cwd = cwd
		depth += 1
		with open(path) as f:
			cwd = os.path.dirname(path)
			for line in f.readlines():
				try:
					parse(line)
				except Exception as e:
					raise Exception(e.message + ": " + path)
		depth -= 1
		cwd = old_cwd
		return

	# chapter
	m = re.match(r"== (.*)", line)
	if m:
		book.append("<장> " + m.group(1) + "\n")
		return

	# section
	m = re.match(r"=== (.*)", line)
	if m:
		book.append("<절> " + m.group(1) + "\n")
		return
	m = re.match(r"==== (.*)", line)
	if m:
		book.append("<소> " + m.group(1) + "\n")
		return
	m = re.match(r"===== (.*)", line)
	if m:
		book.append("<소소> " + m.group(1) + "\n")
		return

	# anchor
	m = re.match(r"^\[\[(.*)\]\]$", line)
	if m:
		book.append("<책갈피 여기는=" + m.group(1) + ">\n")
		return

	# dotted list
	m = re.match(r"^\. .*$", line)
	if m:
		book.append(line)
		return;

	# image-desc
	m = re.match(r"^\..*$", line)
	if m:
		parse_image_desc = line
		return;

	# image
	m = re.match(r"^image::images\/(.*)\[(.*)\]$", line)
	if m:
		if len(parse_image_desc) == 0:
			parse_image_desc = m.group(2)
		parse_image_desc = parse_image_desc.strip(" .\n");
		line = '<그림> %s-%d %s </그림>\n' % (index_fig_ch, index_fig, parse_image_desc)
		figure_dict[m.group(1)] = '%s-%d' % (index_fig_ch, index_fig)
		index_fig += 1

	# index
	ms = re.findall(r"\(\(\((.*?)\)\)\)", line)
	if ms:
		index_set.update(ms)
	line = re.sub(r"\(\(\((.*?)\)\)\)", r"<인덱스 여기는=\1>", line)

	# ref
	line = re.sub(r"<<(.*)>>", r"<책갈피 가리킴=\1>", line)

	# fix http link
	m = re.match(r"(.*)(http.*)\[\](.*)", line);
	if m:
		book.append("%s%s%s\n" % (m.group(1), m.group(2), m.group(3)))
		return;

	parse_image_desc = ''
	book.append(line)

book = []
depth = 1
cwd = '.'
block = []
in_block = ''
index_fig_ch = 0 # 'figure 1-1' for chapter part
index_fig    = 0 # 'figure 1-1' for figure part

asc_files = OrderedDict()

asc_files['1'] = 'book/01-introduction/1-introduction.asc'
asc_files['2'] = 'book/02-git-basics/1-git-basics.asc'
asc_files['3'] = 'book/03-git-branching/1-git-branching.asc'
asc_files['4'] = 'book/04-git-server/1-git-server.asc'
asc_files['5'] = 'book/05-distributed-git/1-distributed-git.asc'
asc_files['6'] = 'book/06-github/1-github.asc'
asc_files['7'] = 'book/07-git-tools/1-git-tools.asc'
asc_files['8'] = 'book/08-customizing-git/1-customizing-git.asc'
asc_files['9'] = 'book/09-git-and-other-scms/1-git-and-other-scms.asc'
asc_files['10'] = 'book/10-git-internals/1-git-internals.asc'
asc_files['A'] = 'book/A-git-in-other-environments/1-git-other-environments.asc'
asc_files['B'] = 'book/B-embedding-git/1-embedding-git.asc'
asc_files['C'] = 'book/C-git-commands/1-git-commands.asc'
asc_files['D'] = 'book/contributors.asc'
asc_files['Index'] = 'book/index.asc'
asc_files['Intro'] = 'book/introduction.asc'
asc_files['Pre'] = 'book/preface.asc'
asc_files['Toc'] = 'book/toc.asc'

for ch in asc_files:
	index_fig = 1
	index_fig_ch = ch
	book = []
	path = cwd + "/" + asc_files[ch]
	with open(path) as f:
		old_cwd = cwd
		for line in f.readlines():
			cwd = os.path.dirname(path)
			parse(line)
		cwd = old_cwd

	out_name = 'publish_' + asc_files[ch].replace('/', '_') + '.txt'
	with open(out_name, 'w') as f:
		print len(book), out_name
		for line in book:
			f.write(line)

with open("publish_book_index_english.txt", 'w') as f:
	for line in sorted(index_set):
		f.write(line + '\n')

# To convert image name to index,
# download images into 'progit2-ko-images' directory
# Make a directory 'images_insight' images to be copied
print 'Rename %d Images...' % len(figure_dict)
for root, dirs, files in os.walk('progit2-ko-images'):
	if not root.endswith('/images'):
		continue
	for filename in files:
		if filename in figure_dict:
			src = os.path.join(root, filename)
			dst = os.path.join('images_insight', '%s_%s' % (figure_dict[filename], filename))
			if not os.path.exists(dst):
				shutil.copy(src, dst)
			continue
		m = re.match(r"^(.*?)@.*$", filename)
		if m:
			prefix = m.group(1) + '.png'
			if prefix in figure_dict:
				src = os.path.join(root, filename)
				dst = os.path.join('images_insight', '%s_%s' % (figure_dict[prefix], filename))
				if not os.path.exists(dst):
					shutil.copy(src, dst)
				continue