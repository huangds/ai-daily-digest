.PHONY: help install test clean lint format

help:  ## 显示帮助信息
	@echo "可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖
	pip install -r requirements.txt
	pip install -e .

install-dev: install  ## 安装开发依赖
	pip install pytest black flake8 mypy

test:  ## 运行测试
	python -m pytest tests/ -v

test-cov:  ## 运行测试并生成覆盖率报告
	python -m pytest tests/ -v --cov=scripts --cov-report=html

lint:  ## 代码风格检查
	flake8 scripts/ tests/

format:  ## 代码格式化
	black scripts/ tests/

type-check:  ## 类型检查
	mypy scripts/

clean:  ## 清理临时文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage
	rm -f scripts/*.json scripts/*.md !scripts/example_output/

run-fetch:  ## 运行 RSS 采集
	python scripts/rss_fetch.py --hours 24

run-digest:  ## 运行完整 AI 评分流程（需要 API Key）
	export GEMINI_API_KEY=$$(cat .env | grep GEMINI_API_KEY | cut -d '=' -f2) && \
	python scripts/rss_digest.py --hours 24 --top-n 8

check: lint type-check test  ## 运行所有检查（lint + type-check + test）

setup: install-dev  ## 初始化开发环境
	cp .env.example .env
	@echo "请编辑 .env 文件，填写你的 API Key"
	@echo "设置完成！运行 'make help' 查看可用命令"

.DEFAULT_GOAL := help
