# LBP Face Recognition

基于均匀局部二值模式（LBP）的 ORL 人脸识别实验，包含基线复现、光照归一化、旋转搜索和距离融合。

## 环境与运行

建议使用 Python 3.11，在仓库根目录执行：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m experiments.orl --data data/ORL --seed 0 --out results/orl_seed0.json
python workshop_baseline.py
python workshop_improved.py
python workshop_final.py
```

## ORL 数据

图片数据不随仓库上传。将 ORL 数据放到 `data/ORL/`，目录应为 `s1` 至 `s40`，每个目录含 `1.pgm` 至 `10.pgm`。可从原项目使用的数据来源 [Face-Recognition-MLP](https://github.com/saeid436/Face-Recognition-MLP) 获取 ORL 文件夹。准备后运行：

```bash
python -m lbpface.datasets data/ORL
```

未准备数据时，依赖 ORL 的测试会跳过。`expected/orl_seed0.json` 保留已有基准结果供回归比较；不同数据副本可能触发指纹检查跳过。

## 项目结构

- `lbpface/`：LBP 编码、区域直方图、距离计算、分类、预处理和可复现性工具。
- `experiments/`：ORL、参数扫描及 FERET 实验。
- `workshop_*.py`：固定数据划分下的基线和改进实验。
- `tests/`：单元测试和 ORL 回归测试。
- `results/`：已有 JSON 和 CSV 实验结果。
- `expected/`：固定的回归结果。
- `docs/original_colab_notes.md`：从原依赖文件整理出的说明和 Colab 操作笔记。

## 实验说明

[中文结果与讲解](LBP实验结果与讲解稿.md) · [English guide](LBP_Results_and_Demonstration_EN.md) · [One-page LaTeX report](LBP_One_Page_Report.tex)

固定划分使用每人的图片 1–5 作为图库，6–10 作为测试。已有结果中，正常图片准确率从 97.5% 提升到 98.0%，强侧光从 70.5% 提升到 95.0%，20° 旋转从 63.0% 提升到 88.0%。这些结论限于所述数据与变换协议。

此项目是离线识别实验，没有登录接口、HTTP 请求认证、密码存储或访问令牌管理。
