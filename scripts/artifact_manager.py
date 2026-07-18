#!/usr/bin/env python3
"""
Artifact Manager for NotebookLM.
Manages generated artifacts across all supported types.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

from notebooklm_wrapper import NotebookLMWrapper, NotebookLMError
from notebook_manager import NotebookLibrary


def json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def get_notebook_id(notebook_id: Optional[str] = None) -> str:
    """Get notebook ID from argument or active notebook."""
    if notebook_id:
        # Check if it's a library ID or direct NotebookLM ID
        library = NotebookLibrary()
        notebook = library.get_notebook(notebook_id)
        if notebook:
            url = notebook.get("url", "")
            if "notebook/" in url:
                parts = url.split("notebook/")
                if len(parts) > 1:
                    return parts[1].split("/")[0].split("?")[0]
        # Assume it's a direct NotebookLM ID
        return notebook_id

    # Use active notebook
    library = NotebookLibrary()
    active = library.get_active_notebook()
    if not active:
        raise ValueError("No active notebook. Run: python scripts/run.py notebook_manager.py activate --id <id>")

    url = active.get("url", "")
    if "notebook/" in url:
        parts = url.split("notebook/")
        if len(parts) > 1:
            return parts[1].split("/")[0].split("?")[0]
    raise ValueError(f"Cannot extract notebook ID from URL: {url}")


async def cmd_list(args):
    """List artifacts in a notebook."""
    notebook_id = get_notebook_id(args.notebook_id)
    artifact_type = args.type
    if artifact_type == "slide-deck":
        artifact_type = "slide_deck"
    if artifact_type == "data-table":
        artifact_type = "data_table"
    if artifact_type == "mind-map":
        artifact_type = "mind_map"

    async with NotebookLMWrapper() as wrapper:
        artifacts = await wrapper.list_artifacts(notebook_id, artifact_type=artifact_type)

    if not artifacts:
        print("No artifacts found.")
        return

    if args.json:
        print(json.dumps(artifacts, indent=2, ensure_ascii=False, default=json_serializer))
        return

    print(f"\n🎨 Artifacts in notebook ({len(artifacts)} total):\n")
    for artifact in artifacts:
        status = str(artifact.get("status", "unknown")).lower()
        status_icon = "✅" if "complete" in status else "⏳"
        print(f"  {status_icon} [{artifact.get('type', 'unknown')}] {artifact.get('title', 'Untitled')}")
        print(f"     ID: {artifact['artifact_id']}")
        if artifact.get("created_at"):
            print(f"     Created: {artifact['created_at']}")
        if artifact.get("url"):
            print(f"     URL: {artifact['url']}")
        print()


async def cmd_get(args):
    """Get details of a specific artifact."""
    notebook_id = get_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        artifact = await wrapper.get_artifact(notebook_id, args.artifact_id)
    print(json.dumps(artifact, indent=2, ensure_ascii=False, default=json_serializer))


async def cmd_delete(args):
    """Delete an artifact."""
    notebook_id = get_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        await wrapper.delete_artifact(notebook_id, args.artifact_id)
    print(f"✅ Deleted artifact: {args.artifact_id}")


def _print_generation_header(title: str, task_fields: dict):
    print(title)
    for key, value in task_fields.items():
        if value:
            print(f"   {key}: {value}")


def _normalize_artifact_type(artifact_type: str) -> str:
    return (
        artifact_type.lower()
        .replace("_", "-")
        .replace("slide-deck", "slide-deck")
        .replace("mind-map", "mind-map")
        .replace("data-table", "data-table")
    )


async def _wait_and_optionally_download(wrapper: NotebookLMWrapper, notebook_id: str, task_id: str, args, artifact_type: str):
    print("\n⏳ Waiting for generation to complete...")
    final = await wrapper.wait_for_artifact(
        notebook_id,
        task_id,
        timeout=args.timeout,
        poll_interval=10,
    )

    if final.get("is_complete"):
        print("✅ Generation complete!")
        if args.output:
            print(f"📥 Downloading to: {args.output}")
            path = await wrapper.download_artifact(
                notebook_id=notebook_id,
                artifact_id=task_id,
                output_path=args.output,
                artifact_type=artifact_type,
                output_format=getattr(args, "format", "json"),
            )
            print(f"✅ Saved to: {path}")
        elif final.get("url"):
            print(f"🔗 URL: {final['url']}")
    elif final.get("is_failed"):
        print(f"❌ Generation failed: {final.get('error', 'Unknown error')}")
        sys.exit(1)


async def cmd_generate_audio(args):
    """Generate audio overview."""
    notebook_id = get_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "🎙️ Starting audio generation...",
            {
                "Format": args.format,
                "Length": args.length,
                "Language": args.language,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_audio(
            notebook_id,
            instructions=args.instructions or args.focus or "",
            audio_format=args.format,
            audio_length=args.length,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "audio")
        else:
            print(json.dumps(result, indent=2))


async def cmd_generate_video(args):
    """Generate video overview."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "🎬 Starting video generation...",
            {
                "Format": args.format,
                "Style": args.style,
                "Language": args.language,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_video(
            notebook_id=notebook_id,
            instructions=args.focus or "",
            video_format=args.format,
            visual_style=args.style,
            language=args.language,
            source_ids=source_ids,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "video")
        else:
            print(json.dumps(result, indent=2))


async def cmd_generate_report(args):
    """Generate report."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "📝 Starting report generation...",
            {
                "Format": args.format,
                "Language": args.language,
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_report(
            notebook_id=notebook_id,
            report_format=args.format,
            custom_prompt=args.prompt or "",
            language=args.language,
            source_ids=source_ids,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "report")
        else:
            print(json.dumps(result, indent=2))


async def cmd_generate_quiz(args):
    """Generate quiz."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "❓ Starting quiz generation...",
            {
                "Count": args.count,
                "Difficulty": args.difficulty,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_quiz(
            notebook_id=notebook_id,
            question_count=args.count,
            difficulty=args.difficulty,
            focus_prompt=args.focus or "",
            source_ids=source_ids,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "quiz")
        else:
            print(json.dumps(result, indent=2))


async def cmd_generate_flashcards(args):
    """Generate flashcards."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "🗂️ Starting flashcards generation...",
            {
                "Difficulty": args.difficulty,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_flashcards(
            notebook_id=notebook_id,
            difficulty=args.difficulty,
            focus_prompt=args.focus or "",
            source_ids=source_ids,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "flashcards")
        else:
            print(json.dumps(result, indent=2))


async def cmd_generate_mindmap(args):
    """Generate mind map."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "🧠 Starting mind map generation...",
            {
                "Source IDs": args.source_ids,
            },
        )
        result = await wrapper.generate_mind_map(
            notebook_id=notebook_id,
            source_ids=source_ids,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=json_serializer))


async def cmd_generate_slides(args):
    """Generate slide deck from notebook content."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "📊 Starting slide deck generation...",
            {
                "Format": args.format,
                "Length": args.length,
                "Language": args.language,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )

        result = await wrapper.generate_slide_deck(
            notebook_id,
            instructions=args.focus or "",
            slide_format=args.format,
            slide_length=args.length,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "slide-deck")
        else:
            print("\n💡 Use --wait to wait for completion, or check status with:")
            print(f"   python scripts/run.py artifact_manager.py status --task-id {task_id}")
            print(json.dumps(result, indent=2))


async def cmd_revise_slides(args):
    """Revise existing slide deck."""
    instructions = []
    for spec in args.slide:
        parts = spec.strip().split(None, 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid --slide value: {spec}. Use: '<number> <instruction>'")
        slide_num = int(parts[0])
        instructions.append({"slide": slide_num, "instruction": parts[1]})

    async with NotebookLMWrapper() as wrapper:
        result = await wrapper.revise_slide_deck(
            artifact_id=args.artifact_id,
            slide_instructions=instructions,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=json_serializer))


async def cmd_generate_infographic(args):
    """Generate an infographic from notebook content."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "🖼️ Starting infographic generation...",
            {
                "Orientation": args.orientation,
                "Detail Level": args.detail_level,
                "Language": args.language,
                "Focus": args.focus,
                "Source IDs": args.source_ids,
            },
        )

        result = await wrapper.generate_infographic(
            notebook_id,
            instructions=args.focus or "",
            orientation=args.orientation,
            detail_level=args.detail_level,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "infographic")
        else:
            print("\n💡 Use --wait to wait for completion, or check status with:")
            print(f"   python scripts/run.py artifact_manager.py status --task-id {task_id}")
            print(json.dumps(result, indent=2))


async def cmd_generate_data_table(args):
    """Generate data table from notebook content."""
    notebook_id = get_notebook_id(args.notebook_id)
    source_ids = [s.strip() for s in args.source_ids.split(",")] if args.source_ids else None

    async with NotebookLMWrapper() as wrapper:
        _print_generation_header(
            "📈 Starting data table generation...",
            {
                "Description": args.description,
                "Language": args.language,
                "Source IDs": args.source_ids,
            },
        )

        result = await wrapper.generate_data_table(
            notebook_id=notebook_id,
            description=args.description,
            language=args.language,
            source_ids=source_ids,
        )

        task_id = result.get("task_id")
        print(f"   Task ID: {task_id}")

        if args.wait:
            await _wait_and_optionally_download(wrapper, notebook_id, task_id, args, "data-table")
        else:
            print(json.dumps(result, indent=2))


async def cmd_status(args):
    """Check status of a generation task."""
    notebook_id = get_notebook_id(args.notebook_id)
    async with NotebookLMWrapper() as wrapper:
        status = await wrapper.get_task_status(notebook_id, args.task_id)

    if status.get("is_complete"):
        print("✅ Generation complete!")
        if status.get("url"):
            print(f"🔗 URL: {status['url']}")
    elif status.get("is_failed"):
        print(f"❌ Generation failed: {status.get('error', 'Unknown error')}")
    else:
        progress = status.get("progress")
        if progress:
            print(f"⏳ In progress: {progress}%")
        else:
            print(f"⏳ Status: {status.get('status', 'processing')}")

    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))


async def cmd_download(args):
    """Download an artifact to local file."""
    notebook_id = get_notebook_id(args.notebook_id)
    artifact_type = _normalize_artifact_type(args.type)

    async with NotebookLMWrapper() as wrapper:
        print(f"📥 Downloading {artifact_type} artifact...")

        if args.artifact_id:
            path = await wrapper.download_artifact(
                notebook_id=notebook_id,
                artifact_id=args.artifact_id,
                output_path=args.output,
                artifact_type=artifact_type,
                output_format=args.format,
            )
        else:
            # Backward-compatible default for audio latest
            if artifact_type == "audio":
                path = await wrapper.download_audio(notebook_id, args.output)
            else:
                print(f"❌ Please specify --artifact-id for {artifact_type} downloads")
                sys.exit(1)

    print(f"✅ Downloaded to: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage NotebookLM artifacts (audio, video, slides, infographics, reports, quiz, flashcards, mind maps, data tables)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    p = subparsers.add_parser("list", help="List all artifacts in a notebook")
    p.add_argument("--notebook-id", help="Notebook ID (uses active if not specified)")
    p.add_argument(
        "--type",
        choices=["audio", "video", "slide-deck", "infographic", "report", "mind-map", "data-table", "quiz", "flashcards"],
        help="Filter by artifact type",
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")

    # Get command
    p = subparsers.add_parser("get", help="Get artifact details")
    p.add_argument("artifact_id", help="Artifact ID")
    p.add_argument("--notebook-id", help="Notebook ID")

    # Delete command
    p = subparsers.add_parser("delete", help="Delete an artifact")
    p.add_argument("artifact_id", help="Artifact ID")
    p.add_argument("--notebook-id", help="Notebook ID")

    # Generate audio command (backward compatible)
    p = subparsers.add_parser("generate", help="Generate audio overview (podcast)")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--instructions", help="Custom instructions")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument(
        "--format",
        choices=["DEEP_DIVE", "BRIEF", "CRITIQUE", "DEBATE"],
        default="DEEP_DIVE",
        help="Audio format",
    )
    p.add_argument(
        "--length",
        choices=["SHORT", "DEFAULT", "LONG"],
        default="DEFAULT",
        help="Audio length",
    )
    p.add_argument("--wait", action="store_true", help="Wait for generation to complete")
    p.add_argument("--output", "-o", help="Download path (requires --wait)")
    p.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")

    # Generate video
    p = subparsers.add_parser("generate-video", help="Generate video overview")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--format", choices=["EXPLAINER", "BRIEF"], default="EXPLAINER")
    p.add_argument("--style", default="AUTO_SELECT", help="Video style")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--output", "-o")
    p.add_argument("--timeout", type=int, default=600)

    # Generate report
    p = subparsers.add_parser("generate-report", help="Generate report")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--format", default="BRIEFING_DOC", help="Report format")
    p.add_argument("--prompt", help="Custom prompt")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--output", "-o")
    p.add_argument("--timeout", type=int, default=600)

    # Generate quiz
    p = subparsers.add_parser("generate-quiz", help="Generate quiz")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--count", type=int, default=2, help="Number of questions")
    p.add_argument("--difficulty", choices=["EASY", "MEDIUM", "HARD"], default="MEDIUM")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--output", "-o")
    p.add_argument("--format", choices=["json", "markdown", "html"], default="json", help="Download output format")
    p.add_argument("--timeout", type=int, default=600)

    # Generate flashcards
    p = subparsers.add_parser("generate-flashcards", help="Generate flashcards")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--difficulty", choices=["EASY", "MEDIUM", "HARD"], default="MEDIUM")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--output", "-o")
    p.add_argument("--format", choices=["json", "markdown", "html"], default="json", help="Download output format")
    p.add_argument("--timeout", type=int, default=600)

    # Generate mind map
    p = subparsers.add_parser("generate-mindmap", help="Generate mind map")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--source-ids", help="Comma-separated source IDs")

    # Generate slides
    p = subparsers.add_parser("generate-slides", help="Generate slide deck")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument(
        "--format",
        choices=["DETAILED_DECK", "PRESENTER_SLIDES"],
        default="DETAILED_DECK",
        help="Slide format",
    )
    p.add_argument(
        "--length",
        choices=["SHORT", "DEFAULT"],
        default="DEFAULT",
        help="Slide deck length",
    )
    p.add_argument("--wait", action="store_true", help="Wait for generation to complete")
    p.add_argument("--output", "-o", help="Download path (requires --wait)")
    p.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")

    # Revise slides
    p = subparsers.add_parser("revise-slides", help="Revise a slide deck artifact")
    p.add_argument("artifact_id", help="Slide deck artifact ID")
    p.add_argument("--slide", action="append", required=True, help="Slide instruction: '<number> <instruction>'")

    # Generate infographic
    p = subparsers.add_parser("generate-infographic", help="Generate infographic")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--focus", help="Focus prompt")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument(
        "--orientation",
        choices=["LANDSCAPE", "PORTRAIT", "SQUARE"],
        default="LANDSCAPE",
        help="Infographic orientation",
    )
    p.add_argument(
        "--detail-level",
        choices=["CONCISE", "STANDARD", "DETAILED"],
        default="STANDARD",
        help="Detail level",
    )
    p.add_argument("--wait", action="store_true", help="Wait for generation to complete")
    p.add_argument("--output", "-o", help="Download path (requires --wait)")
    p.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")

    # Generate data table
    p = subparsers.add_parser("generate-data-table", help="Generate data table")
    p.add_argument("description", help="Description of desired data table")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--language", default="en", help="Language code")
    p.add_argument("--source-ids", help="Comma-separated source IDs")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--output", "-o")
    p.add_argument("--timeout", type=int, default=600)

    # Status command
    p = subparsers.add_parser("status", help="Check generation task status")
    p.add_argument("--task-id", required=True, help="Task ID from generation command")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument("--json", action="store_true", help="Output as JSON")

    # Download command
    p = subparsers.add_parser("download", help="Download an artifact")
    p.add_argument("output", help="Output file path")
    p.add_argument("--artifact-id", help="Artifact ID (required for non-audio)")
    p.add_argument("--notebook-id", help="Notebook ID")
    p.add_argument(
        "--type",
        choices=["audio", "video", "slide-deck", "infographic", "report", "mind-map", "data-table", "quiz", "flashcards"],
        default="audio",
        help="Artifact type",
    )
    p.add_argument("--format", choices=["json", "markdown", "html"], default="json", help="For quiz/flashcards")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "list": cmd_list,
        "get": cmd_get,
        "delete": cmd_delete,
        "generate": cmd_generate_audio,
        "generate-video": cmd_generate_video,
        "generate-report": cmd_generate_report,
        "generate-quiz": cmd_generate_quiz,
        "generate-flashcards": cmd_generate_flashcards,
        "generate-mindmap": cmd_generate_mindmap,
        "generate-slides": cmd_generate_slides,
        "revise-slides": cmd_revise_slides,
        "generate-infographic": cmd_generate_infographic,
        "generate-data-table": cmd_generate_data_table,
        "status": cmd_status,
        "download": cmd_download,
    }

    try:
        asyncio.run(cmd_map[args.command](args))
        return 0
    except NotebookLMError as e:
        print(f"❌ [{e.code}]: {e.message}")
        if e.recovery:
            print(f"🔧 Recovery: {e.recovery}")
        return 1
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
