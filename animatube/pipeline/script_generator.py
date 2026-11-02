from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from animatube.pipeline.models import Script, ScriptScene, Storyboard, StoryboardScene

logger = logging.getLogger(__name__)

DEVOPS_DEFAULT_TOPIC = "How to Become a DevOps Engineer in 2027 – Complete Beginner Roadmap"
DEVOPS_DEFAULT_AUDIENCE = (
    "Indian beginners, freshers, students, QA engineers, system administrators, "
    "and IT support engineers transitioning into DevOps. Language: Simple English."
)


def generate_devops_roadmap_script() -> Script:
    """Returns the vetted, high-retention production script for DevOps 2027."""
    scenes = [
        ScriptScene(
            id="scene_01",
            title="The 2027 DevOps Trap (Hook)",
            narration=(
                "Why are you wasting your next six months before learning what five DevOps tools actually matter in 2027? "
                "If you search online today, you find endless roadmaps listing fifty different tools. "
                "That overload is why so many beginners get discouraged and quit before deploying their first real app."
            ),
            visual_description="Sprawling 50-node roadmap diagram collapsing into 5 core pillars. Bold counter ticking 2027.",
            on_screen_elements=["50-Tool Chaos", "5 Core Pillars", "2027 Countdown"],
            target_duration_seconds=15.0,
            diagram_type="pillars_overview",
        ),
        ScriptScene(
            id="scene_02",
            title="What DevOps Actually Does (The 2 AM Crash)",
            narration=(
                "To understand why companies value DevOps, imagine an Indian tech startup on a Friday evening. "
                "The developers write code on their laptops and send it to Operations. At two AM, the live servers crash "
                "because background libraries don't match. DevOps destroys that wall by automating the entire delivery pipeline."
            ),
            visual_description="Split screen of developer closing laptop vs operations team troubleshooting late-night crash.",
            on_screen_elements=["Developer Machine", "Production Crash", "Automated Conveyor Belt"],
            target_duration_seconds=20.0,
            diagram_type="devops_flow",
        ),
        ScriptScene(
            id="scene_03",
            title="Pillar 1: Linux Command-Line Fundamentals",
            narration=(
                "Pillar one is Linux. The vast majority of production cloud infrastructure runs on Linux distributions. "
                "You don't need to be a kernel hacker. Master file permissions with chmod, process inspection with top and kill, "
                "reading logs in var-log, and writing small Bash scripts to automate routine system checks."
            ),
            visual_description="Terminal console displaying process hierarchy, file permissions, and active Bash script execution.",
            on_screen_elements=["Linux Terminal", "chmod / chown", "top / kill", "Bash Script"],
            target_duration_seconds=25.0,
            diagram_type="terminal",
        ),
        ScriptScene(
            id="scene_04",
            title="Pillar 2: Git & Version Control",
            narration=(
                "Pillar two is Git and GitHub. Beyond basic commit and push, real DevOps teams use Git to store configuration "
                "and infrastructure templates. You must master branching strategies, resolving merge conflicts, pull requests, "
                "and setting up Webhooks to trigger automated pipelines whenever new code is merged."
            ),
            visual_description="Git branching tree diagram showing feature branches merging into main and triggering a webhook.",
            on_screen_elements=["Git Branch Tree", "Merge Conflict", "Pull Request", "Webhook Trigger"],
            target_duration_seconds=25.0,
            diagram_type="git_tree",
        ),
        ScriptScene(
            id="scene_05",
            title="Pillar 3: Docker & Containerization",
            narration=(
                "Pillar three is Docker. Instead of software failing across different environments, Docker bundles your application, "
                "runtime, and dependencies into a lightweight image. Master writing clean Dockerfiles, understanding images versus containers, "
                "mapping ports, and using Docker Compose for multi-container apps."
            ),
            visual_description="Docker architecture diagram packaging code and runtime into standardized container boxes.",
            on_screen_elements=["Standardized Container", "Dockerfile Syntax", "Docker Compose"],
            target_duration_seconds=25.0,
            diagram_type="docker",
        ),
        ScriptScene(
            id="scene_06",
            title="Pillar 4: Jenkins & CI/CD Pipelines",
            narration=(
                "Pillar four is Jenkins for Continuous Integration and Continuous Delivery. Jenkins acts as an automated robot butler. "
                "The second code is pushed to GitHub, Jenkins pulls it, runs automated tests, builds the Docker image, "
                "and prepares it for deployment—stopping bugs before they ever touch production."
            ),
            visual_description="Automated digital assembly line showing Code Push, Unit Tests, Docker Build, and Staging Deploy.",
            on_screen_elements=["Code Push", "Automated Testing", "Docker Build", "Deployment"],
            target_duration_seconds=25.0,
            diagram_type="jenkins",
        ),
        ScriptScene(
            id="scene_07",
            title="Pillar 5: AWS Cloud Infrastructure",
            narration=(
                "Pillar five is AWS. For entry-level DevOps, focus on five foundational services: EC2 virtual servers, S3 storage, "
                "IAM security permissions, custom VPC networking, and Amazon ECR for container registries. "
                "Set up CloudWatch billing alarms on day one so you get notified before costs accumulate."
            ),
            visual_description="AWS Cloud architecture topology diagram showing VPC, EC2 instances, S3 bucket, and IAM roles.",
            on_screen_elements=["Amazon EC2", "Amazon S3", "AWS IAM", "Custom VPC", "Billing Alarms"],
            target_duration_seconds=25.0,
            diagram_type="aws",
        ),
        ScriptScene(
            id="scene_08",
            title="The 6-Month Study Plan & Portfolio Capstone",
            narration=(
                "Here is your six-month roadmap: Month one Linux, Month two Git and Bash, Month three Docker, Month four Jenkins, "
                "and Month five AWS. In Month six, build one end-to-end project: code pushed to GitHub automatically triggers Jenkins, "
                "builds a Docker image, and deploys it onto an AWS EC2 instance. Live working projects beat paper certificates every time."
            ),
            visual_description="Month-by-month calendar roadmap transitioning into complete end-to-end capstone architecture.",
            on_screen_elements=["6-Month Timeline", "GitHub-to-AWS Pipeline", "Portfolio Project"],
            target_duration_seconds=25.0,
            diagram_type="roadmap",
        ),
        ScriptScene(
            id="scene_09",
            title="Conclusion & Actionable Next Steps",
            narration=(
                "You do not need to learn fifty tools to begin your DevOps journey in 2027. "
                "Focus on these five core pillars, practice hands-on in the terminal every day, and build projects you can explain with confidence. "
                "Comment below with which step you are starting this week, and subscribe for our live pipeline tutorial."
            ),
            visual_description="Summary recap screen with companion GitHub checklist callout and interactive prompt.",
            on_screen_elements=["5 Pillars Recap", "GitHub Checklist Callout", "Subscribe & Comment"],
            target_duration_seconds=15.0,
            diagram_type="pillars_overview",
        ),
    ]

    return Script(
        title=DEVOPS_DEFAULT_TOPIC,
        target_audience=DEVOPS_DEFAULT_AUDIENCE,
        scenes=scenes,
    )


class OllamaScriptGenerator:
    """Client for generating video scripts via local Ollama inference."""

    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        """Checks if the local Ollama instance is reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_script(
        self,
        topic: str = DEVOPS_DEFAULT_TOPIC,
        audience: str = DEVOPS_DEFAULT_AUDIENCE,
        use_fallback_if_unavailable: bool = True,
    ) -> Script:
        """Generates a structured video script using Ollama or vetted deterministic fallback."""
        if not self.is_available():
            if use_fallback_if_unavailable:
                logger.info("Ollama unavailable; using deterministic production script.")
                return generate_devops_roadmap_script()
            raise RuntimeError(f"Ollama server not reachable at {self.host}")

        prompt = (
            f"You are a YouTube educational scriptwriter. Create a structured video script on:\n"
            f"Topic: {topic}\n"
            f"Target Audience: {audience}\n\n"
            f"Output ONLY a valid JSON object with the following schema:\n"
            f"{{\n"
            f'  "title": "{topic}",\n'
            f'  "target_audience": "{audience}",\n'
            f'  "scenes": [\n'
            f"    {{\n"
            f'      "id": "scene_01",\n'
            f'      "title": "Scene Title",\n'
            f'      "narration": "Full spoken voiceover text in simple English.",\n'
            f'      "visual_description": "Detailed description of graphics.",\n'
            f'      "on_screen_elements": ["Element 1", "Element 2"],\n'
            f'      "target_duration_seconds": 20.0,\n'
            f'      "diagram_type": "terminal|git_tree|docker|jenkins|aws|roadmap|pillars_overview"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}\n"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                response_text = data.get("response", "{}")
                parsed = json.loads(response_text)
                return Script.from_dict(parsed)
        except Exception as exc:
            if use_fallback_if_unavailable:
                logger.warning("Ollama inference failed (%s); falling back to default.", exc)
                return generate_devops_roadmap_script()
            raise


def create_storyboard_from_script(script: Script, fps: int = 30) -> Storyboard:
    """Transforms a Script into a Storyboard with initial frame allocations."""
    storyboard_scenes: list[StoryboardScene] = []
    for scene in script.scenes:
        duration_sec = max(5.0, scene.target_duration_seconds)
        frames = int(round(duration_sec * fps))
        sb_scene = StoryboardScene(
            scene_id=scene.id,
            title=scene.title,
            duration_seconds=duration_sec,
            duration_frames=frames,
            diagram_type=scene.diagram_type,
        )
        storyboard_scenes.append(sb_scene)

    return Storyboard(
        title=script.title,
        fps=fps,
        width=1920,
        height=1080,
        scenes=storyboard_scenes,
    )
