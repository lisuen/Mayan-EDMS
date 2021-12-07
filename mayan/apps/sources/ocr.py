# -*- coding: utf-8 -*-

import easyocr
import cv2
import numpy as np
import difflib
from shapely import geometry
import jieba
import jieba.posseg as pseg
from PIL import Image

# jieba.enable_paddle()


def if_inPoly(polygon, Points):
    line = geometry.LineString(polygon)
    point = geometry.Point(Points)
    polygon = geometry.Polygon(line)
    return polygon.contains(point)


# 获取关键字开始位置
def keyword_start(word_list, position_list, keyword):
    for word in word_list:
        similarity = difflib.SequenceMatcher(None, word, keyword).quick_ratio()
        # 与关键字相似度超过50%
        if similarity >= 0.5:
            # 从文本框左下角开始
            return position_list[word_list.index(word)]


def get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list):
    selected_list = []
    # 检测范围,逆时针写入坐标
    area = [(left_bottom_x, left_bottom_y), (right_top_x, left_bottom_y), (right_top_x, right_top_y),
            (left_bottom_x, right_top_y)]
    for i in range(0, len(position_list)):
        if if_inPoly(area, (position_list[i][0][0], position_list[i][0][1])) & if_inPoly(area, (
                position_list[i][1][0], position_list[i][1][1])) \
                & if_inPoly(area, (position_list[i][2][0], position_list[i][2][1])) & if_inPoly(area, (
                position_list[i][3][0], position_list[i][3][1])):
            selected_list.append(word_list[i])
    return selected_list


def cut_name(s):
    person_list = ['丁志宇', '傅广卷', '郭洪雨', '郑永卫', '李伟平', '徐金胜', '吴锐', '郭昊亮', '陈新国', '包泮旺', '徐羊敏', '王丰平', '马芹纲', '吴根强',
                   '丁海洋', '郑军华', '高能', '周义程', '耿驰远']
    name = ''
    words = pseg.cut(s, use_paddle=True)
    for word, flag in words:
        for person in person_list:
            if difflib.SequenceMatcher(None, word, person).quick_ratio() >= 0.5:
                return person
    # for word, flag in words:
    #     if difflib.SequenceMatcher(None, word, '海洋').quick_ratio() >= 0.6:
    #         return '丁海洋'
    #     if flag == 'PER' or flag == 'nr':
    #         name = word
    #         return name
    return name

cadList = []

# 创建reader对象
reader = easyocr.Reader(['ch_sim', 'en'])

def ocrFile(file_path):

    # 解决图片路径中中文问题
    # img = cv2.imdecode(np.fromfile(file, dtype=np.uint8), -1)
    # 读取图像
    # result = reader.readtext(file_path, canvas_size=4096)
    result = reader.readtext(file_path, canvas_size=1080)
    print(result)


    word_list = []
    position_list = []
    sketch_list = []
    table_list = []

    for j in result:
        position = j[0]
        word = j[1]
        recognitionRate = j[2]
        position_list.append(position)
        word_list.append(word)
        if '示意' in word or '大样' in word or '设计图' in word or '截面' in word or '剖面' in word or '平面' in word or '立面' in word or '配置图' in word or '布置图' in word:
            if len(word) <= 18:
                sketch_list.append(word)

        if '数量表' in word or '尺寸表' in word or '材料表' in word:
            table_list.append(word)

    department = keyword_start(word_list, position_list, '浙江省交通规划设计研究院') if keyword_start(word_list, position_list, '浙江省交通规划设计研究院') is not None else [[640, 6383], [3339, 6383], [3339, 6661], [640, 6661]]
    # 提取图纸名字
    left_bottom_x = department[0][0] + 2480
    left_bottom_y = department[1][1] - 50
    right_top_x = left_bottom_x + 1900
    right_top_y = left_bottom_y + 500
    # print(left_bottom_x, left_bottom_y, right_top_x, right_top_y)
    drawing_name = ''.join(
        get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list,
                               word_list))

    # 提取设计者
    left_bottom_x = department[0][0] + 4180
    left_bottom_y = department[1][1] - 150
    right_top_x = left_bottom_x + 1300
    right_top_y = left_bottom_y + 500
    designer = cut_name(''.join(
        get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list)))

    # 提取复核者
    left_bottom_x = department[0][0] + 5320
    left_bottom_y = department[1][1] - 150
    right_top_x = left_bottom_x + 1300
    right_top_y = left_bottom_y + 500
    reviewer = cut_name(''.join(
        get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list)))

    # 提取审核者
    left_bottom_x = department[0][0] + 6250
    left_bottom_y = department[1][1] - 150
    right_top_x = left_bottom_x + 2000
    right_top_y = left_bottom_y + 500
    viewer = cut_name(''.join(
        get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list)))

    # 提取图号
    left_bottom_x = department[0][0] + 8100
    left_bottom_y = department[1][1] - 150
    right_top_x = left_bottom_x + 900
    right_top_y = left_bottom_y + 500
    drawing_num = ' '.join(
        get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list)).strip('图号')

    note = keyword_start(word_list, position_list, '注') if keyword_start(word_list, position_list,
                                                                         '注') is not None else keyword_start(
        word_list, position_list, '说明')
    if note is not None:
        # 提取注解或说明
        left_bottom_x = note[0][0] - 50
        left_bottom_y = note[0][1] - 50
        right_top_x = left_bottom_x + 3300
        right_top_y = left_bottom_y + 1800
        annotation = ''.join(
            get_selected_area_word(left_bottom_x, left_bottom_y, right_top_x, right_top_y, position_list, word_list))
    else:
        annotation = ''

    sketch = ','.join(sketch_list)
    sheet = ','.join(table_list)
    # 如果图号在注释中被识别
    if len(annotation) != 0 and '图号' in annotation:
        s = annotation.split('图号', 1)
        annotation = s[0]
        if len(drawing_num) == 0:
            drawing_num = s[1]

    if '审核' in annotation or '复核' in annotation or viewer in annotation or reviewer in annotation:
        annotation = annotation.strip('审核').strip('复核').strip(viewer).strip(reviewer)

    eachList = [drawing_name, drawing_num, designer, viewer, reviewer, annotation, sketch, sheet]
    ocrResult = '图纸名:' + drawing_name + ' 图号:' + drawing_num + ' 设计者:' + designer + ' 审核者:' + viewer + ' 复审者:' + reviewer + ' 包含图示:' + sketch + ' 包含表格:' + sheet
    # print(eachList)
    # cadList.append(eachList)
    return ocrResult

