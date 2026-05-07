import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


repo_root = Path(__file__).resolve().parents[1]
runtime_node = Path(
    "/Users/dw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
)


class visual_ppt_deck_builder_tests(unittest.TestCase):
    def node_executable(self):
        if runtime_node.is_file():
            return str(runtime_node)
        return "node"

    def test_deck_spec_builds_editable_pptx_with_media(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            asset_path = tmp_path / "transparent_asset.png"
            image = Image.new("RGBA", (240, 180), (0, 0, 0, 0))
            for y_index in range(40, 140):
                for x_index in range(55, 185):
                    image.putpixel((x_index, y_index), (32, 140, 210, 255))
            image.save(asset_path)

            spec_path = tmp_path / "deck_spec.json"
            output_path = tmp_path / "visual_ppt_deck.pptx"
            spec_path.write_text(
                json.dumps(
                    {
                        "title": "AI 视觉素材生产线",
                        "subtitle": "透明素材到可编辑 PPTX",
                        "author": "Codex",
                        "theme": {
                            "background": "F7F4EF",
                            "foreground": "17202A",
                            "accent": "1F8A70",
                            "accent_2": "E76F51",
                            "muted": "6B7280",
                            "font_face": "Aptos",
                        },
                        "slides": [
                            {
                                "layout": "title",
                                "title": "AI 视觉素材生产线",
                                "subtitle": "先定主题，再定风格，最后交付 PPTX",
                            },
                            {
                                "layout": "image_text",
                                "title": "透明素材是视觉组件",
                                "claim": "透明素材应该像积木一样被复用，而不是被烤死在整页截图里。",
                                "body": "每个素材都可以叠加到网页、PPT、海报和产品界面。",
                                "bullets": ["纯色底生图", "透明背景清理", "组合到页面"],
                                "image": str(asset_path),
                                "source": "内部流程样例，2026-05",
                            },
                            {
                                "layout": "bar_chart",
                                "title": "素材复用效率",
                                "claim": "可编辑图表让同一套素材能进入更多业务文档。",
                                "body": "用形状绘制的图表可继续编辑。",
                                "chart": {
                                    "labels": ["网站", "PPT", "App"],
                                    "values": [42, 68, 55],
                                    "unit": "%",
                                    "source": "示例数据，仅用于流程测试",
                                },
                            },
                            {
                                "layout": "closing",
                                "title": "交付物",
                                "body": "可编辑 PPTX + 透明素材 + 风格说明。",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_visual_pptx.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                env={**os.environ, "NODE_PATH": self.node_modules_path()},
            )

            self.assertTrue(output_path.is_file())
            self.assertGreater(output_path.stat().st_size, 10_000)
            with zipfile.ZipFile(output_path) as pptx_zip:
                entries = set(pptx_zip.namelist())
                slide_entries = [entry for entry in entries if entry.startswith("ppt/slides/slide")]
                media_entries = [entry for entry in entries if entry.startswith("ppt/media/")]
                self.assertGreaterEqual(len(slide_entries), 4)
                self.assertTrue(media_entries)
                self.assertIn("ppt/presentation.xml", entries)
                slide_one_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
                self.assertNotIn("<a:t>Topic</a:t>", slide_one_xml)
                self.assertNotIn("<a:t>Style</a:t>", slide_one_xml)
                self.assertNotIn("<a:t>Assets</a:t>", slide_one_xml)

    def test_deck_spec_requires_slides(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            spec_path = tmp_path / "bad_spec.json"
            output_path = tmp_path / "bad.pptx"
            spec_path.write_text(json.dumps({"title": "Bad"}), encoding="utf-8")

            result = subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_visual_pptx.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output_path),
                ],
                text=True,
                capture_output=True,
                env={**os.environ, "NODE_PATH": self.node_modules_path()},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("slides", result.stderr)
            self.assertFalse(output_path.exists())

    def test_style_candidate_helper_writes_real_image_prompt_packet(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_dir = tmp_path / "style-candidates"
            topic = "2026 AI 应用趋势调研"

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_style_candidates.js"
                    ),
                    "--output-dir",
                    str(output_dir),
                    "--topic",
                    topic,
                    "--allow-placeholder-backgrounds",
                ],
                check=True,
            )

            self.assertFalse(list(output_dir.glob("*.svg")))
            self.assertFalse(list(output_dir.glob("style-board-*")))
            self.assertFalse((output_dir / "style-overview.svg").exists())
            self.assertFalse((output_dir / "generated").exists())
            self.assertTrue((output_dir / "style-candidates.md").is_file())
            visual_qa_path = output_dir / "style-visual-qa.json"
            self.assertTrue(visual_qa_path.is_file())
            visual_qa = json.loads(visual_qa_path.read_text(encoding="utf-8"))
            self.assertTrue(visual_qa["ok"])
            self.assertEqual(visual_qa["candidate_count"], 8)
            self.assertEqual(visual_qa["failed_count"], 0)
            self.assertIn("readability", visual_qa["gate"])
            self.assertIn("background_overlap", visual_qa["gate"])
            for item in visual_qa["items"]:
                self.assertEqual(item["status"], "pass")
                self.assertGreaterEqual(item["text_zone_score"], 0.8)
                self.assertGreaterEqual(item["chart_zone_score"], 0.8)
                self.assertEqual(item["has_background_overlap_risk"], False)
                self.assertNotIn("no custom background image", item["reason"])
            design_qa_path = output_dir / "style-design-qa.json"
            self.assertTrue(design_qa_path.is_file())
            design_qa = json.loads(design_qa_path.read_text(encoding="utf-8"))
            self.assertTrue(design_qa["ok"])
            self.assertEqual(design_qa["candidate_count"], 8)
            self.assertEqual(design_qa["failed_count"], 0)
            self.assertIn("visual_focus", design_qa["gate"])
            for item in design_qa["items"]:
                self.assertEqual(item["status"], "pass")
                self.assertGreaterEqual(item["visual_focus_score"], 0.42)
                self.assertGreaterEqual(item["edge_signature_score"], 0.28)
                self.assertEqual(item["has_flat_background_risk"], False)
            spec_path = output_dir / "style-candidate-spec.json"
            self.assertTrue(spec_path.is_file())
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            self.assertEqual(spec["candidate_count"], 8)
            self.assertEqual(spec["delivery_contract"], "editable_pptx_samples_with_png_previews")
            self.assertEqual(spec["topic"], topic)
            self.assertEqual(spec["background_asset_policy"]["source"], "test_only_placeholder")
            self.assertEqual(spec["background_asset_policy"]["commercial_ready"], False)
            self.assertIn("不能进入正式展示", spec["background_asset_policy"]["restriction"])
            self.assertIn("PPTX 样板", spec["preview_rule"])
            self.assertIn("可编辑", spec["ppt_contract"])
            self.assertIn("融合式版面", spec["visual_quality_contract"])
            self.assertIn("禁止大白框", spec["visual_quality_contract"])
            self.assertEqual(spec["large_surface_policy"]["max_large_content_panels"], 0)
            self.assertEqual(spec["large_surface_policy"]["max_large_chart_panels"], 0)
            self.assertEqual(spec["large_surface_policy"]["max_framed_metric_tiles"], 0)
            self.assertIn("背景留白", spec["visual_quality_contract"])
            self.assertEqual(spec["readable_area_policy"]["text_safe_zones_required"], True)
            self.assertEqual(spec["readable_area_policy"]["chart_safe_zones_required"], True)
            self.assertEqual(spec["readable_area_policy"]["low_detail_transition_required"], True)
            self.assertGreaterEqual(spec["readable_area_policy"]["min_body_text_contrast_ratio"], 4.5)
            self.assertGreaterEqual(spec["readable_area_policy"]["min_chart_stroke_contrast_ratio"], 3.0)
            self.assertIn("不能靠加框补救", spec["readable_area_policy"]["anti_rescue_box_rule"])
            self.assertEqual(spec["coordinate_blueprint_policy"]["coordinate_unit"], "inches_16_9")
            self.assertEqual(spec["coordinate_blueprint_policy"]["blueprint_required_before_background"], True)
            self.assertEqual(spec["coordinate_blueprint_policy"]["background_prompt_must_include_zone_coordinates"], True)
            self.assertIn("效果图拆解", spec["coordinate_blueprint_policy"]["layout_first_rule"])
            self.assertEqual(spec["style_reference_policy"]["reference_image_required_before_decomposition"], True)
            self.assertEqual(spec["style_reference_policy"]["clean_background_after_reference"], True)
            self.assertEqual(spec["style_reference_policy"]["editable_reconstruction_required"], True)
            self.assertIn("先直出完整效果图", spec["style_reference_policy"]["workflow_rule"])
            expected_names = [
                "简约高级",
                "活泼动漫",
                "数据分析",
                "国潮东方",
                "未来科技",
                "编辑杂志",
                "SaaS 产品",
                "投资人叙事",
            ]
            self.assertEqual([candidate["name"] for candidate in spec["candidates"]], expected_names)
            self.assertIn("style_diversity_policy", spec)
            self.assertGreaterEqual(spec["style_diversity_policy"]["min_unique_layout_variants"], 6)
            self.assertIn("visual_focus_policy", spec)
            self.assertEqual(spec["visual_focus_policy"]["visible_visual_anchor_required"], True)
            self.assertGreaterEqual(spec["visual_focus_policy"]["min_visual_focus_score"], 0.42)
            layout_variants = {candidate["layout_variant"] for candidate in spec["candidates"]}
            self.assertGreaterEqual(len(layout_variants), 6)
            title_fonts = {candidate["typography_system"]["title_font_face"] for candidate in spec["candidates"]}
            self.assertGreaterEqual(len(title_fonts), 3)
            seen_sample_paths = set()
            for candidate in spec["candidates"]:
                self.assertIn("layout_variant", candidate)
                self.assertIn("title_treatment", candidate)
                self.assertIn("metric_treatment", candidate)
                self.assertIn("chart_treatment", candidate)
                self.assertIn("background_visual_anchor", candidate)
                self.assertIn("visual_focus_asset_strategy", candidate)
                self.assertEqual(candidate["sample_slide_spec"]["layout_variant"], candidate["layout_variant"])
                self.assertTrue(candidate["pptx_sample_path"].endswith(".pptx"))
                self.assertTrue(candidate["preview_png_path"].endswith(".png"))
                self.assertNotIn(candidate["preview_png_path"], seen_sample_paths)
                seen_sample_paths.add(candidate["preview_png_path"])
                pptx_path = output_dir / candidate["pptx_sample_path"]
                preview_path = output_dir / candidate["preview_png_path"]
                self.assertTrue(pptx_path.is_file())
                self.assertTrue(preview_path.is_file())
                self.assertGreater(pptx_path.stat().st_size, 8_000)
                self.assertGreater(preview_path.stat().st_size, 1_000)
                background_path = output_dir / candidate["background_asset_path"]
                self.assertTrue(background_path.is_file())
                self.assertGreater(background_path.stat().st_size, 5_000)
                with zipfile.ZipFile(pptx_path) as pptx_zip:
                    slide_xml = "\n".join(
                        pptx_zip.read(entry).decode("utf-8", errors="ignore")
                        for entry in pptx_zip.namelist()
                        if entry.startswith("ppt/slides/slide")
                    )
                    self.assertIn(topic, slide_xml)
                    self.assertIn(candidate["sample_content"]["section_title"], slide_xml)
                    self.assertIn(candidate["sample_content"]["body"], slide_xml)
                    for metric in candidate["sample_content"]["metrics"]:
                        self.assertIn(metric["value"], slide_xml)
                        self.assertIn(metric["label"], slide_xml)
                    self.assertNotIn('prst="roundRect"', slide_xml)
                prompt_path = output_dir / candidate["prompt_file"]
                self.assertTrue(prompt_path.is_file())
                prompt_content = prompt_path.read_text(encoding="utf-8")
                self.assertIn("Codex image generation", prompt_content)
                self.assertIn("clean background image only", prompt_content)
                self.assertIn("Coordinate blueprint", prompt_content)
                self.assertIn("text_zone", prompt_content)
                self.assertIn("chart_zone", prompt_content)
                self.assertIn("Remove all readable text", prompt_content)
                self.assertNotIn("Use the following sample Chinese content", prompt_content)
                self.assertNotIn("Chart labels:", prompt_content)
                self.assertIn(topic, prompt_content)
                reference_prompt_path = output_dir / candidate["style_reference_prompt_file"]
                self.assertTrue(reference_prompt_path.is_file())
                reference_prompt_content = reference_prompt_path.read_text(encoding="utf-8")
                self.assertIn("full-page style reference image", reference_prompt_content)
                self.assertIn("完整效果图", reference_prompt_content)
                self.assertIn(topic, reference_prompt_content)
                self.assertEqual(len(candidate["palette"]), 5)
                self.assertGreaterEqual(len(candidate["best_for"]), 3)
                self.assertGreaterEqual(len(candidate["raster_layers"]), 2)
                self.assertGreaterEqual(len(candidate["transparent_assets"]), 2)
                self.assertGreaterEqual(len(candidate["editable_layers"]), 4)
                self.assertIn("sample_content", candidate)
                self.assertEqual(candidate["sample_content"]["title"], topic)
                self.assertGreaterEqual(len(candidate["sample_content"]["bullets"]), 3)
                self.assertGreaterEqual(len(candidate["sample_content"]["metrics"]), 3)
                self.assertGreaterEqual(len(candidate["sample_content"]["chart_labels"]), 3)
                self.assertIn("editable_text_contract", candidate)
                self.assertIn("asset_layer_contract", candidate)
                self.assertIn("surface_strategy", candidate)
                self.assertIn("no_plain_white_box_contract", candidate)
                self.assertIn("readability_contract", candidate)
                self.assertIn("safe_zone_plan", candidate)
                self.assertIn("coordinate_blueprint", candidate)
                self.assertIn("style_reference_prompt_file", candidate)
                self.assertIn("clean_background_prompt_file", candidate)
                self.assertIn("visual_decomposition", candidate)
                self.assertIn("reconstruction_layers", candidate)
                self.assertIn("typography_system", candidate)
                self.assertIn("chart_language", candidate)
                self.assertIn("效果图", candidate["visual_decomposition"]["source"])
                self.assertGreaterEqual(len(candidate["reconstruction_layers"]), 4)
                self.assertIn("large_surface_count", candidate)
                blueprint = candidate["coordinate_blueprint"]
                self.assertEqual(blueprint["unit"], "inches")
                self.assertAlmostEqual(blueprint["slide"]["width"], 13.333, places=3)
                self.assertAlmostEqual(blueprint["slide"]["height"], 7.5, places=2)
                for zone_name in [
                    "title_zone",
                    "text_zone",
                    "chart_zone",
                    "metrics_zone",
                    "visual_focus_zone",
                    "protected_empty_zone",
                ]:
                    self.assertIn(zone_name, blueprint["zones"])
                    zone = blueprint["zones"][zone_name]
                    for key in ["x", "y", "w", "h"]:
                        self.assertIn(key, zone)
                        self.assertIsInstance(zone[key], (int, float))
                    self.assertGreater(zone["w"], 0)
                    self.assertGreater(zone["h"], 0)
                    self.assertLessEqual(zone["x"] + zone["w"], 13.333 + 0.001)
                    self.assertLessEqual(zone["y"] + zone["h"], 7.5 + 0.001)
                self.assertEqual(candidate["large_surface_count"]["content_panels"], 0)
                self.assertEqual(candidate["large_surface_count"]["chart_panels"], 0)
                self.assertEqual(candidate["large_surface_count"]["framed_metric_tiles"], 0)
                self.assertIn("sample_slide_spec", candidate)
                self.assertIn("文本", candidate["editable_text_contract"])
                self.assertIn("背景", candidate["asset_layer_contract"])
                self.assertIn("融合", candidate["surface_strategy"])
                self.assertIn("大白框", candidate["no_plain_white_box_contract"])
                self.assertIn("字色", candidate["readability_contract"])
                self.assertIn("过渡", candidate["readability_contract"])
                self.assertIn("text_zone", candidate["safe_zone_plan"])
                self.assertIn("chart_zone", candidate["safe_zone_plan"])
                self.assertIn("integrated_surface_strategy", candidate["sample_slide_spec"])
                self.assertIn("readable_area_strategy", candidate["sample_slide_spec"])
                self.assertIn("coordinate_blueprint_strategy", candidate["sample_slide_spec"])
                self.assertIn("reference_reconstruction_strategy", candidate["sample_slide_spec"])
                self.assertEqual(candidate["sample_slide_spec"]["forbidden_large_panel_count"], 0)
                self.assertEqual(candidate["sample_slide_spec"]["forbidden_framed_metric_tile_count"], 0)
            markdown = (output_dir / "style-candidates.md").read_text(encoding="utf-8")
            self.assertIn("PPTX 样板", markdown)
            self.assertIn("PNG 预览", markdown)
            self.assertIn("文本可编辑", markdown)
            self.assertIn("真实 PPT", markdown)
            self.assertIn("融合式版面", markdown)
            self.assertIn("禁止大白框", markdown)
            self.assertIn("大面积正文容器：0", markdown)
            self.assertIn("大面积图表容器：0", markdown)
            self.assertIn("指标描边框：0", markdown)
            self.assertIn("阅读安全区", markdown)
            self.assertIn("图表安全区", markdown)
            self.assertIn("坐标蓝图", markdown)
            self.assertIn("效果图母稿", markdown)
            self.assertIn("clean background", markdown)
            self.assertIn("反拆", markdown)
            self.assertIn("title_zone", markdown)
            self.assertIn("不能靠加框补救", markdown)
            self.assertIn("2026 AI 应用趋势调研", markdown)
            for banned_text in ["Topic", "Style", "Assets", "TODO", "TBD", "占位"]:
                self.assertNotIn(banned_text, markdown)

    def test_style_candidate_helper_rejects_missing_real_backgrounds_by_default(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "style-candidates"
            result = subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_style_candidates.js"
                    ),
                    "--output-dir",
                    str(output_dir),
                    "--topic",
                    "2026 AI 应用趋势调研",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("真实生图背景", result.stderr)
            self.assertIn("--background-source-dir", result.stderr)
            self.assertFalse((output_dir / "style-candidate-spec.json").exists())

    def test_commercial_deck_quality_gate_accepts_rich_spec(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            spec_path = tmp_path / "commercial_spec.json"
            report_path = tmp_path / "qa_report.json"
            spec_path.write_text(
                json.dumps(self.commercial_spec(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "validate_deck_quality.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--report",
                    str(report_path),
                ],
                check=True,
            )

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["ok"])
            self.assertEqual(report["slide_count"], 8)
            self.assertGreaterEqual(report["layout_count"], 6)

    def test_commercial_deck_quality_gate_rejects_missing_claims_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            spec = self.commercial_spec()
            spec["slides"][2].pop("claim")
            spec["slides"][4].pop("source")
            spec["slides"][4]["chart"].pop("source")
            spec["slides"][0]["kicker"] = "Topic"
            spec_path = tmp_path / "bad_commercial_spec.json"
            report_path = tmp_path / "bad_qa_report.json"
            spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "validate_deck_quality.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--report",
                    str(report_path),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertTrue(any("claim" in error for error in report["errors"]))
            self.assertTrue(any("source" in error for error in report["errors"]))
            self.assertTrue(any("placeholder" in error for error in report["errors"]))

    def test_reference_anime_trend_layout_builds_editable_pptx_without_large_panels(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            background_path = tmp_path / "clean_background.png"
            image = Image.new("RGB", (1600, 900), (238, 247, 255))
            image.save(background_path)

            spec_path = tmp_path / "anime_reference_spec.json"
            output_path = tmp_path / "anime_reference_sample.pptx"
            spec_path.write_text(
                json.dumps(
                    {
                        "title": "2026 AI 应用趋势调研",
                        "subtitle": "从智能助手到业务协同",
                        "author": "Codex",
                        "theme": {
                            "background": "EEF7FF",
                            "foreground": "0B1B4D",
                            "accent": "2F80ED",
                            "accent_2": "FF6F82",
                            "muted": "52637A",
                            "font_face": "Aptos",
                        },
                        "slides": [
                            {
                                "layout": "reference_visual_trend",
                                "background_image": str(background_path),
                                "coordinate_blueprint": {
                                    "title_zone": {"x": 1.0, "y": 1.08, "w": 5.1, "h": 0.62},
                                    "subtitle_zone": {"x": 1.02, "y": 1.78, "w": 4.6, "h": 0.42},
                                    "bullet_zone": {"x": 1.02, "y": 2.46, "w": 4.95, "h": 2.02},
                                    "metrics_zone": {"x": 2.05, "y": 5.12, "w": 3.95, "h": 1.08},
                                    "chart_title_zone": {"x": 6.82, "y": 1.7, "w": 3.2, "h": 0.38},
                                    "chart_zone": {"x": 6.7, "y": 2.38, "w": 5.08, "h": 3.7},
                                },
                                "title": "2026 AI 应用趋势调研",
                                "subtitle": "从智能助手到业务协同",
                                "bullets": [
                                    {"title": "学习成本降低", "body": "AI 工具更易上手，知识获取与技能成长更高效。"},
                                    {"title": "内容生产提速", "body": "AI 提升内容产出效率，释放更多创造力与价值。"},
                                    {"title": "团队流程重构", "body": "AI 协同优化流程，驱动组织高效运转与创新。"},
                                ],
                                "metrics": [
                                    {"value": "73%", "label": "企业试点"},
                                    {"value": "3x", "label": "内容提效"},
                                    {"value": "2026", "label": "落地窗口"},
                                ],
                                "chart": {
                                    "title": "AI 应用综合趋势指数",
                                    "labels": ["2023\n探索期", "2024\n成长期", "2025\n加速期", "2026E\n规模化"],
                                    "values": [58, 72, 86, 96],
                                    "unit": "",
                                    "source": "示例数据，仅用于视觉样张",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_visual_pptx.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                env={**os.environ, "NODE_PATH": self.node_modules_path()},
            )

            self.assertTrue(output_path.is_file())
            with zipfile.ZipFile(output_path) as pptx_zip:
                entries = set(pptx_zip.namelist())
                slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
                self.assertTrue(any(entry.startswith("ppt/media/") for entry in entries))
                for expected_text in [
                    "2026",
                    "AI 应用趋势调研",
                    "从智能助手到业务协同",
                    "学习成本降低",
                    "内容生产提速",
                    "团队流程重构",
                    "73%",
                    "3x",
                    "企业试点",
                    "AI 应用综合趋势指数",
                    "探索期",
                    "规模化",
                ]:
                    self.assertIn(expected_text, slide_xml)
                self.assertNotIn('prst="roundRect"', slide_xml)
                self.assertGreaterEqual(slide_xml.count('prst="rect"'), 5)
                self.assertGreaterEqual(slide_xml.count('prst="line"'), 5)
                self.assertGreaterEqual(slide_xml.count('prst="ellipse"'), 6)

    def test_reference_visual_trend_layout_variants_render_distinct_page_grammar(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            background_path = tmp_path / "clean_background.png"
            image = Image.new("RGB", (1600, 900), (240, 244, 248))
            image.save(background_path)

            variants = [
                "minimal_left_report",
                "future_dashboard_focus",
                "oriental_vertical_scroll",
                "editorial_feature_story",
            ]
            signatures = set()

            for variant in variants:
                spec_path = tmp_path / f"{variant}.json"
                output_path = tmp_path / f"{variant}.pptx"
                spec_path.write_text(
                    json.dumps(
                        {
                            "title": "2026 AI 应用趋势调研",
                            "author": "Codex",
                            "theme": {
                                "background": "F0F4F8",
                                "foreground": "111827",
                                "accent": "2563EB",
                                "accent_2": "0F766E",
                                "muted": "4B5563",
                                "font_face": "Aptos",
                            },
                            "slides": [
                                {
                                    "layout": "reference_visual_trend",
                                    "layout_variant": variant,
                                    "background_image": str(background_path),
                                    "title": "2026 AI 应用趋势调研",
                                    "subtitle": "企业智能化进入规模落地窗口",
                                    "bullets": [
                                        {"title": "场景深入流程", "body": "AI 从单点工具进入营销、客服、研发和知识管理。"},
                                        {"title": "组织能力分化", "body": "数据治理、权限边界和评审机制决定真实收益。"},
                                        {"title": "ROI 口径升级", "body": "从效率提升转向周期缩短、质量稳定和经验沉淀。"},
                                    ],
                                    "metrics": [
                                        {"value": "73%", "label": "企业试点"},
                                        {"value": "3x", "label": "内容提效"},
                                        {"value": "2026", "label": "规模窗口"},
                                    ],
                                    "chart": {
                                        "title": "趋势指数",
                                        "labels": ["工具", "流程", "数据", "组织"],
                                        "values": [54, 68, 76, 91],
                                        "source": "示例数据，仅用于视觉样张",
                                    },
                                }
                            ],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                subprocess.run(
                    [
                        self.node_executable(),
                        str(
                            repo_root
                            / "skills"
                            / "visual-ppt-deck-builder"
                            / "scripts"
                            / "build_visual_pptx.js"
                        ),
                        "--spec",
                        str(spec_path),
                        "--output",
                        str(output_path),
                    ],
                    check=True,
                    env={**os.environ, "NODE_PATH": self.node_modules_path()},
                )

                with zipfile.ZipFile(output_path) as pptx_zip:
                    slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
                    self.assertIn("2026", slide_xml)
                    self.assertIn("AI 应用趋势调研", slide_xml)
                    self.assertIn("趋势指数", slide_xml)
                    self.assertNotIn('prst="roundRect"', slide_xml)
                    signatures.add(
                        (
                            slide_xml.count('prst="rect"'),
                            slide_xml.count('prst="line"'),
                            slide_xml.count('prst="ellipse"'),
                            slide_xml.count("<a:t>"),
                        )
                    )

            self.assertEqual(len(signatures), len(variants))

    def test_reference_layout_accepts_dark_overlay_style_colors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            background_path = tmp_path / "dark_clean_background.png"
            image = Image.new("RGB", (1600, 900), (8, 20, 48))
            image.save(background_path)

            spec_path = tmp_path / "dark_reference_spec.json"
            output_path = tmp_path / "dark_reference_sample.pptx"
            spec_path.write_text(
                json.dumps(
                    {
                        "title": "2026 AI 应用趋势调研",
                        "author": "Codex",
                        "theme": {
                            "background": "06142E",
                            "foreground": "F5F9FF",
                            "accent": "2BD3FF",
                            "accent_2": "8D6BFF",
                            "muted": "AFC0D8",
                            "font_face": "Aptos",
                        },
                        "slides": [
                            {
                                "layout": "reference_anime_trend",
                                "background_image": str(background_path),
                                "coordinate_blueprint": {
                                    "title_zone": {"x": 0.8, "y": 0.78, "w": 5.35, "h": 0.68},
                                    "subtitle_zone": {"x": 0.82, "y": 1.5, "w": 4.9, "h": 0.34},
                                    "bullet_zone": {"x": 0.82, "y": 2.15, "w": 5.18, "h": 2.2},
                                    "metrics_zone": {"x": 0.88, "y": 5.48, "w": 4.75, "h": 0.95},
                                    "chart_title_zone": {"x": 7.08, "y": 1.3, "w": 3.8, "h": 0.38},
                                    "chart_zone": {"x": 6.72, "y": 1.92, "w": 4.8, "h": 3.9},
                                },
                                "overlay_style": {
                                    "subtitle_color": "CFE5FF",
                                    "bullet_title_color": "F5F9FF",
                                    "bullet_body_color": "B8C8DE",
                                    "bullet_icon_texts": ["01", "02", "03"],
                                    "title_font_size": 30,
                                    "subtitle_font_size": 13,
                                    "bullet_title_font_size": 12,
                                    "bullet_body_font_size": 8,
                                    "metric_value_font_size": 18,
                                    "metric_label_font_size": 7.5,
                                    "chart_title_font_size": 12,
                                    "chart_tick_font_size": 6.8,
                                    "chart_label_font_size": 7.1,
                                    "chart_value_font_size": 8.4,
                                    "chart_bar_transparency": 20,
                                    "metrics_divider_color": "456B9D",
                                    "metric_label_color": "D8E6F8",
                                    "chart_title_color": "F5F9FF",
                                    "chart_grid_color": "456B9D",
                                    "chart_tick_color": "A9BEDA",
                                    "chart_label_color": "CFE5FF",
                                    "chart_value_color": "F5F9FF",
                                    "chart_source_color": "8EA6C8",
                                    "chart_bar_colors": ["2BD3FF", "4E8DFF", "8D6BFF", "16E0B3"]
                                },
                                "title": "2026 AI 应用趋势调研",
                                "subtitle": "企业级智能化进入规模落地窗口",
                                "bullets": [
                                    {"title": "场景从试点转向流程", "body": "AI 能力开始嵌入营销、客服、研发和知识管理。"},
                                    {"title": "组织能力成为分水岭", "body": "数据治理、权限边界和评审机制决定真实收益。"},
                                    {"title": "ROI 需要重新定义", "body": "从单点提效转向周期缩短、质量稳定和经验沉淀。"}
                                ],
                                "metrics": [
                                    {"value": "68%", "label": "流程嵌入"},
                                    {"value": "2.4x", "label": "协同提效"},
                                    {"value": "2026", "label": "规模窗口"}
                                ],
                                "chart": {
                                    "title": "趋势指数",
                                    "labels": ["工具", "流程", "数据", "组织"],
                                    "values": [54, 68, 76, 91],
                                    "source": "示例数据，仅用于视觉样张"
                                }
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_visual_pptx.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                env={**os.environ, "NODE_PATH": self.node_modules_path()},
            )

            with zipfile.ZipFile(output_path) as pptx_zip:
                slide_xml = pptx_zip.read("ppt/slides/slide1.xml").decode("utf-8")
                for expected_color in [
                    "CFE5FF",
                    "B8C8DE",
                    "456B9D",
                    "A9BEDA",
                    "8EA6C8",
                    "16E0B3",
                ]:
                    self.assertIn(expected_color, slide_xml)
                for expected_icon in ["01", "02", "03"]:
                    self.assertIn(f"<a:t>{expected_icon}</a:t>", slide_xml)
                for expected_size in [
                    'sz="3000"',
                    'sz="1300"',
                    'sz="1200"',
                    'sz="800"',
                    'sz="1800"',
                    'sz="750"',
                    'sz="680"',
                    'sz="710"',
                    'sz="840"',
                ]:
                    self.assertIn(expected_size, slide_xml)
                self.assertIn('alpha val="80000"', slide_xml)
                for old_light_layout_color in ["3C4F73", "587092", "52637A"]:
                    self.assertNotIn(old_light_layout_color, slide_xml)

    def test_preview_helper_writes_slide_svgs_and_contact_sheet(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            spec_path = tmp_path / "commercial_spec.json"
            preview_dir = tmp_path / "preview"
            spec_path.write_text(
                json.dumps(self.commercial_spec(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    self.node_executable(),
                    str(
                        repo_root
                        / "skills"
                        / "visual-ppt-deck-builder"
                        / "scripts"
                        / "build_deck_preview.js"
                    ),
                    "--spec",
                    str(spec_path),
                    "--output-dir",
                    str(preview_dir),
                ],
                check=True,
            )

            self.assertTrue((preview_dir / "contact-sheet.svg").is_file())
            slides = sorted(preview_dir.glob("slide-*.svg"))
            self.assertEqual(len(slides), 8)
            contact_sheet = (preview_dir / "contact-sheet.svg").read_text(encoding="utf-8")
            slide_two = (preview_dir / "slide-02.svg").read_text(encoding="utf-8")
            self.assertIn("AI 编程工具", contact_sheet)
            self.assertIn("<tspan", slide_two)
            self.assertNotIn("…", slide_two)

    def node_modules_path(self):
        return "/Users/dw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"

    def commercial_spec(self):
        return {
            "title": "AI 编程工具进入企业研发流程的商业化落地方案",
            "subtitle": "从个人提效走向组织级交付能力",
            "author": "Codex",
            "theme": {
                "background": "F5F7FA",
                "foreground": "17202A",
                "accent": "1769AA",
                "accent_2": "D65A31",
                "muted": "667085",
                "panel": "FFFFFF",
                "font_face": "Aptos",
            },
            "slides": [
                {
                    "layout": "title",
                    "title": "AI 编程工具进入企业研发流程的商业化落地方案",
                    "subtitle": "面向 CTO、研发负责人和业务负责人",
                    "kicker": "组织级研发提效方案",
                },
                {
                    "layout": "executive_summary",
                    "title": "一页结论",
                    "claim": "AI 编程工具的商业价值不在“多写代码”，而在缩短需求到上线的反馈回路。",
                    "points": [
                        {"label": "01", "title": "先收口场景", "body": "从测试补齐、遗留代码解释、内部工具开发切入。"},
                        {"label": "02", "title": "再建治理", "body": "权限、代码审查、数据边界和产出验收必须同步上线。"},
                        {"label": "03", "title": "最后规模化", "body": "用指标证明收益，再扩到更多团队和业务线。"},
                    ],
                    "source": "项目方法论样例，2026-05",
                },
                {
                    "layout": "content",
                    "title": "当前痛点",
                    "claim": "企业真正卡住的不是工具采购，而是缺少可复制的接入流程。",
                    "body": "个人试用很快能看到效率，但组织推广会遇到权限、质量、知识沉淀和审查责任问题。",
                    "bullets": ["需求表达不稳定", "代码审查压力上升", "知识只留在对话里", "试点收益难量化"],
                    "source": "企业研发流程访谈模板，2026-05",
                },
                {
                    "layout": "architecture",
                    "title": "组织级接入架构",
                    "claim": "把 AI 编程工具放进研发流水线，而不是放任它成为个人外挂。",
                    "layers": [
                        {"title": "业务入口", "body": "需求卡片、设计稿、故障单、数据分析任务"},
                        {"title": "AI 工作台", "body": "代码生成、测试补齐、文档同步、变更说明"},
                        {"title": "治理层", "body": "权限、审计、上下文脱敏、模型路由、成本控制"},
                        {"title": "交付层", "body": "代码仓库、CI、评审、发布、知识库沉淀"},
                    ],
                    "source": "内部架构假设，2026-05",
                },
                {
                    "layout": "metrics",
                    "title": "价值测算口径",
                    "claim": "先用三个可观测指标判断试点是否值得扩大。",
                    "metrics": [
                        {"value": "20-35%", "label": "需求到 PR 周期下降", "body": "仅统计试点场景，不外推到全部研发。"},
                        {"value": "15-25%", "label": "测试补齐耗时下降", "body": "以同类模块和同类复杂度对比。"},
                        {"value": "2周", "label": "最小试点周期", "body": "能覆盖一次完整需求闭环。"},
                    ],
                    "chart": {
                        "labels": ["开发", "测试", "文档", "评审"],
                        "values": [28, 22, 34, 12],
                        "unit": "%",
                        "source": "示例测算模型，非外部事实",
                    },
                    "source": "示例测算模型，非外部事实",
                },
                {
                    "layout": "comparison",
                    "title": "工具路线对比",
                    "claim": "不同路线适合不同成熟度，不能只按模型热度采购。",
                    "items": [
                        {"title": "IDE 助手", "body": "上手最快，适合个人提效和局部代码生成。"},
                        {"title": "Agent 工作流", "body": "适合跨文件任务，但需要更强审查和回滚机制。"},
                        {"title": "企业平台", "body": "治理完整，但接入成本和组织改造更高。"},
                    ],
                    "source": "路线对比框架，2026-05",
                },
                {
                    "layout": "roadmap",
                    "title": "90 天落地路线",
                    "claim": "商业化落地要小步验证，避免一上来全员铺开。",
                    "phases": [
                        {"period": "第 1-2 周", "title": "选场景", "body": "挑选高频、低风险、可衡量的研发任务。"},
                        {"period": "第 3-4 周", "title": "跑闭环", "body": "形成需求、生成、审查、发布、复盘链路。"},
                        {"period": "第 5-8 周", "title": "建治理", "body": "补权限、审计、成本、知识库沉淀。"},
                        {"period": "第 9-12 周", "title": "扩团队", "body": "按指标决定扩展范围和培训节奏。"},
                    ],
                    "source": "试点计划样例，2026-05",
                },
                {
                    "layout": "risk_next_steps",
                    "title": "风险与下一步",
                    "claim": "下一步不是买更多账号，而是把试点做成可验收的业务项目。",
                    "risks": ["敏感代码和数据进入不受控上下文", "生成代码绕过评审责任", "只看速度不看返工成本"],
                    "actions": ["确定 2 个试点团队", "定义 5 个验收指标", "建立 AI 产出审查清单"],
                    "source": "项目治理清单，2026-05",
                },
            ],
        }


if __name__ == "__main__":
    unittest.main()
