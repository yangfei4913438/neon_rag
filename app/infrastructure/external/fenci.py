#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/11 00:54
@Author : YangFei
@File   : fenci.py
@Desc   : 文本在向量化之后，会先经过分词处理，增加召回数据的准确性
"""

import os
from pathlib import Path
import logging
import unicodedata
from langdetect import detect, LangDetectException, DetectorFactory
from core.consts import STOPWORD_SET
import hanlp
import opencc
from collections import Counter
from functools import lru_cache


class Fenci:
    """ 分词 """

    # 加载中文和多语言分词模型
    def __init__(self):
        """ 初始化分词器 """
        # 设置语言检测的随机种子，保证结果一致性
        DetectorFactory.seed = 0
        # 初始化繁体转简体转换器
        self.t2s_converter = opencc.OpenCC('t2s')  # 繁体转简体
        self.s2t_converter = opencc.OpenCC('s2t')  # 简体转繁体

        # 显式指定模型缓存目录（与 Docker 中的 HANLP_HOME 一致）
        hanlp_model_dir = Path(os.getenv("HANLP_HOME", "/neon_assistant/.hanlp"))

        # 初始化时加载模型（已经在 docker 构建的时候进行了预加载，这里直接使用即可）
        logging.info("加载中文分词模型...")
        # 加载中文分词模型
        self.chinese_tokenizer = hanlp.load(
            hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH,
            cache_dir=hanlp_model_dir  # 显式指定路径
        )
        logging.info("中文分词模型加载完成.")

        # 加载多语言分词模型
        logging.info("加载多语言分词模型...")
        self.multilingual_tokenizer = hanlp.load(
            hanlp.pretrained.tok.UD_TOK_MMINILMV2L6,
            cache_dir=hanlp_model_dir  # 显式指定路径
        )
        logging.info('多语言分词模型加载完成.')

    def _clean_tokens(self, tokens: list[str]) -> list[str]:
        """ 清洗分词列表 """
        return [
            token
            for token in tokens
            if token not in STOPWORD_SET  # 去除停用词
               and token.strip()  # 去除空白字符
               and not self._is_punctuation(token)  # 去除标点符号
        ]

    @staticmethod
    def _is_punctuation(token: str):
        """ 判断字符是否为标点符号，支持中英文
        :param token: 单个字符或字符串
        :return: 如果是标点符号则返回 True，否则返回 False
        """
        return len(token) == 1 and unicodedata.category(token).startswith('P')

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        检测文本语言。

        :param text: 输入文本
        :return: 检测到的语言代码（如 'zh-cn', 'en' 等）
        """
        # 极端情况：文本太短，langdetect 可能不准
        if len(text.strip()) < 3:
            # 对超短文本使用简单判断
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return 'zh-cn'

        try:
            return detect(text)
        except LangDetectException:
            # 如果语言检测失败，默认使用多语言分词器
            return "unknown"

    def _convert_and_tokenize(self, text, lang):
        """ 繁简转换和分词 """
        logging.debug(f"繁简转换和分词: lang={lang}")

        # 如果是繁体中文，先转换为简体中文
        if lang in ['zh-tw', 'zh-hant']:
            logging.debug(f"使用繁体中文分词器处理")
            # 转换为简体中文
            text = self.t2s_converter.convert(text)
            # 使用简体中文分词器
            tokens = self.chinese_tokenizer(text)
            # 分词结果转换回繁体中文
            return [self.s2t_converter.convert(token) for token in tokens]
        elif lang == 'zh-cn':
            logging.debug(f"使用中文分词器处理")
            # 简体中文，直接分词
            return self.chinese_tokenizer(text)
        else:
            try:
                logging.debug(f"使用多语言分词器处理")
                # 其他语言，使用多语言分词器
                return self.multilingual_tokenizer(text)
            except Exception as e:
                logging.error(f"多语言分词器处理失败: {e}, 尝试使用中文分词器处理")
                # 简体中文，直接分词
                return self.chinese_tokenizer(text)

    def _split_tokens(self, text: str) -> list[str]:
        """ 分割文本 """
        logging.debug(f"开始分割文本: {text[:20]}...")

        # 检测语言
        lang = self._detect_language(text)
        logging.debug(f"检测到的文本语言: {lang}")

        # 转换并分词
        tokens = self._convert_and_tokenize(text, lang)
        if not tokens:
            logging.debug("分词结果为空")
            return []

        # 清洗分词列表，返回结果
        return self._clean_tokens(tokens)

    def get_top_n_tokens(self, text: str, top_n: int = 10) -> list[str]:
        """
        获取出现次数最多的 N 个分词（不包含次数）。

        :param text: 输入文本
        :param top_n: 返回的分词数量，默认为 10
        :return: 出现次数最多的 N 个分词，格式为 [token1, token2, ...]
        """
        # 分词并清洗
        tokens = self._split_tokens(text)
        if not tokens:
            logging.debug("分词结果为空")
            return []

        # 统计词频
        token_counts = Counter(tokens)

        # 提取出现次数最多的 N 个分词, 并转换为小写
        top_tokens = [str(token).lower() for token, _ in token_counts.most_common(top_n)]
        logging.debug(f"提取的分词: {top_tokens}")

        # 返回结果
        return top_tokens


@lru_cache()
def get_fenci_client():
    """使用 lru_cache 实现单例"""
    return Fenci()
