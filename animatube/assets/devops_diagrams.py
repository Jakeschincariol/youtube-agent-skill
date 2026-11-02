from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)


def _ensure_qapp() -> QGuiApplication:
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv if hasattr(sys, "argv") and sys.argv else ["animatube"])
    return app


class DevOpsDiagramGenerator:
    """Generates crisp 1080p educational visual assets and diagrams using PySide6 QPainter."""

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        _ensure_qapp()
        self.width = width
        self.height = height

    def _create_base_canvas(self, title: str, subtitle: str) -> tuple[QImage, QPainter]:
        image = QImage(self.width, self.height, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Background gradient: Dark GitHub/VSCode slate
        gradient = QLinearGradient(0, 0, self.width, self.height)
        gradient.setColorAt(0.0, QColor("#090d16"))
        gradient.setColorAt(1.0, QColor("#121b2d"))
        painter.fillRect(0, 0, self.width, self.height, gradient)

        # Subtle top accent bar
        accent_gradient = QLinearGradient(0, 0, self.width, 0)
        accent_gradient.setColorAt(0.0, QColor("#38bdf8"))
        accent_gradient.setColorAt(0.5, QColor("#818cf8"))
        accent_gradient.setColorAt(1.0, QColor("#34d399"))
        painter.fillRect(0, 0, self.width, 8, accent_gradient)

        # Header Title
        title_font = QFont("Segoe UI", 42)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor("#f8fafc")))
        painter.drawText(QRectF(80, 50, self.width - 160, 65), int(Qt.AlignmentFlag.AlignLeft), title)

        # Subtitle
        sub_font = QFont("Segoe UI", 22)
        painter.setFont(sub_font)
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.drawText(QRectF(80, 115, self.width - 160, 45), int(Qt.AlignmentFlag.AlignLeft), subtitle)

        # Top-right 2027 Badge
        badge_rect = QRectF(self.width - 260, 55, 180, 48)
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        painter.setBrush(QBrush(QColor(56, 189, 248, 30)))
        painter.drawRoundedRect(badge_rect, 10, 10)
        badge_font = QFont("Segoe UI", 20)
        badge_font.setBold(True)
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor("#38bdf8")))
        painter.drawText(badge_rect, int(Qt.AlignmentFlag.AlignCenter), "DEVOPS 2027")

        return image, painter

    def generate_pillars_overview(self, output_path: str | Path) -> Path:
        """Diagram 1: 5 Core Pillars (Linux, Git, Docker, Jenkins, AWS)."""
        image, painter = self._create_base_canvas(
            "The 5 Core Pillars of Modern DevOps",
            "Master these foundational tools before touching advanced cluster tools",
        )

        pillars = [
            ("1. Linux", "OS & Terminal", "Permissions, logs, processes, Bash scripts", "#38bdf8"),
            ("2. Git", "Version Control", "Branches, PRs, merge conflicts, Webhooks", "#f97316"),
            ("3. Docker", "Containers", "Dockerfiles, compose, image registries", "#0284c7"),
            ("4. Jenkins", "CI/CD Automation", "Pipelines, automated test runs, artifacts", "#eab308"),
            ("5. AWS", "Cloud Infrastructure", "EC2, S3, IAM, custom VPC networking", "#f59e0b"),
        ]

        card_width = 320
        card_height = 480
        gap = 35
        start_x = 80
        start_y = 220

        for i, (p_title, category, desc, color_hex) in enumerate(pillars):
            x = start_x + i * (card_width + gap)
            card_rect = QRectF(x, start_y, card_width, card_height)

            # Card background
            painter.setPen(QPen(QColor(color_hex), 2))
            painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
            painter.drawRoundedRect(card_rect, 16, 16)

            # Header color accent block
            header_rect = QRectF(x, start_y, card_width, 100)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.drawRoundedRect(header_rect, 16, 16)
            # Flatten bottom corners of header
            painter.drawRect(QRectF(x, start_y + 80, card_width, 20))

            # Pillar Title
            h_font = QFont("Segoe UI", 24)
            h_font.setBold(True)
            painter.setFont(h_font)
            painter.setPen(QPen(QColor("#0f172a")))
            painter.drawText(header_rect, int(Qt.AlignmentFlag.AlignCenter), p_title)

            # Category
            c_font = QFont("Segoe UI", 20)
            c_font.setBold(True)
            painter.setFont(c_font)
            painter.setPen(QPen(QColor(color_hex)))
            painter.drawText(QRectF(x + 20, start_y + 130, card_width - 40, 40), int(Qt.AlignmentFlag.AlignCenter), category)

            # Description
            d_font = QFont("Segoe UI", 18)
            painter.setFont(d_font)
            painter.setPen(QPen(QColor("#cbd5e1")))
            painter.drawText(QRectF(x + 25, start_y + 190, card_width - 50, 240), int(Qt.AlignmentFlag.AlignTop) | int(Qt.TextFlag.TextWordWrap), desc)

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target

    def generate_terminal_diagram(self, output_path: str | Path) -> Path:
        """Diagram 2: Linux Terminal Console Diagnostic View."""
        image, painter = self._create_base_canvas(
            "Pillar 1: Linux Command-Line Fundamentals",
            "95%+ of production servers run Linux — Command-line diagnostic view",
        )

        term_rect = QRectF(140, 200, 1640, 780)

        # Terminal body
        painter.setPen(QPen(QColor("#334155"), 2))
        painter.setBrush(QBrush(QColor("#0a0f1d")))
        painter.drawRoundedRect(term_rect, 16, 16)

        # Terminal Titlebar
        bar_rect = QRectF(140, 200, 1640, 50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(bar_rect, 16, 16)
        painter.drawRect(QRectF(140, 230, 1640, 20))

        # Mac/Linux window buttons
        colors = ["#ef4444", "#eab308", "#22c55e"]
        for idx, col in enumerate(colors):
            painter.setBrush(QBrush(QColor(col)))
            painter.drawEllipse(QRectF(170 + idx * 30, 218, 16, 16))

        # Window title
        tb_font = QFont("Consolas", 18)
        painter.setFont(tb_font)
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.drawText(bar_rect, int(Qt.AlignmentFlag.AlignCenter), "devops@ubuntu-server: ~ (bash)")

        # Terminal content
        lines = [
            ("devops@ubuntu:~$ ", "#38bdf8", "chmod 755 deploy.sh && chown -R appuser:appgroup /var/www/app", "#f8fafc"),
            ("devops@ubuntu:~$ ", "#38bdf8", "systemctl status nginx.service", "#f8fafc"),
            ("● nginx.service - High Performance Web Server", "#22c55e", "", "#f8fafc"),
            ("   Loaded: loaded (/lib/systemd/system/nginx.service; enabled)", "#94a3b8", "", "#f8fafc"),
            ("   Active: active (running) since Mon 2027-01-15 09:30:12 IST; 4h 12m ago", "#22c55e", "", "#f8fafc"),
            ("devops@ubuntu:~$ ", "#38bdf8", "ps aux | grep node", "#f8fafc"),
            ("appuser   14820  1.2  4.8  982104 142050 ?  Sl  09:31  1:15 node /app/server.js", "#cbd5e1", "", "#f8fafc"),
            ("devops@ubuntu:~$ ", "#38bdf8", "tail -n 3 /var/log/nginx/access.log", "#f8fafc"),
            ('192.168.1.45 - - [15/Jan/2027:13:42:01 +0530] "GET /api/v1/health HTTP/1.1" 200 48', "#e2e8f0", "", "#f8fafc"),
            ('192.168.1.92 - - [15/Jan/2027:13:42:05 +0530] "POST /api/v1/order HTTP/1.1" 201 112', "#e2e8f0", "", "#f8fafc"),
            ("devops@ubuntu:~$ ", "#38bdf8", "curl -I http://localhost:8080/api/health", "#f8fafc"),
            ("HTTP/1.1 200 OK | Content-Type: application/json | Status: HEALTHY █", "#34d399", "", "#f8fafc"),
        ]

        text_font = QFont("Consolas", 20)
        painter.setFont(text_font)
        y = 290
        for prompt, p_col, cmd, c_col in lines:
            x = 180
            painter.setPen(QPen(QColor(p_col)))
            painter.drawText(x, y, prompt)
            x += len(prompt) * 12
            painter.setPen(QPen(QColor(c_col)))
            painter.drawText(x, y, cmd)
            y += 42

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target

    def generate_git_diagram(self, output_path: str | Path) -> Path:
        """Diagram 3: Git Branching & Webhook Automation Architecture."""
        image, painter = self._create_base_canvas(
            "Pillar 2: Git Workflows & Automated Webhooks",
            "How code triggers continuous delivery from feature branch to production",
        )

        # Branch Lines
        main_y = 400
        feat_y = 650

        # Main branch line
        painter.setPen(QPen(QColor("#38bdf8"), 6))
        painter.drawLine(200, main_y, 1400, main_y)

        # Feature branch line
        painter.setPen(QPen(QColor("#a855f7"), 6))
        painter.drawLine(400, main_y, 550, feat_y)
        painter.drawLine(550, feat_y, 1050, feat_y)
        painter.drawLine(1050, feat_y, 1200, main_y)

        # Commits on main
        commits_main = [
            (250, "v1.0.0"),
            (400, "Branch Point"),
            (750, "Hotfix"),
            (1200, "Merge PR #42"),
            (1380, "v1.1.0"),
        ]
        for cx, label in commits_main:
            painter.setPen(QPen(QColor("#f8fafc"), 4))
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawEllipse(QPointF(cx, main_y), 18, 18)

            painter.setPen(QPen(QColor("#e2e8f0")))
            lbl_font = QFont("Segoe UI", 16)
            lbl_font.setBold(True)
            painter.setFont(lbl_font)
            painter.drawText(QRectF(cx - 70, main_y - 50, 140, 30), int(Qt.AlignmentFlag.AlignCenter), label)

        # Commits on feature branch
        commits_feat = [
            (650, "Commit A"),
            (850, "Commit B"),
            (1050, "Pass Tests"),
        ]
        for cx, label in commits_feat:
            painter.setPen(QPen(QColor("#f8fafc"), 4))
            painter.setBrush(QBrush(QColor("#9333ea")))
            painter.drawEllipse(QPointF(cx, feat_y), 18, 18)

            lbl_font = QFont("Segoe UI", 16)
            lbl_font.setBold(True)
            painter.setFont(lbl_font)
            painter.setPen(QPen(QColor("#e2e8f0")))
            painter.drawText(QRectF(cx - 70, feat_y + 30, 140, 30), int(Qt.AlignmentFlag.AlignCenter), label)

        # Webhook Trigger Box
        wh_rect = QRectF(1450, 310, 380, 240)
        painter.setPen(QPen(QColor("#22c55e"), 3))
        painter.setBrush(QBrush(QColor("#064e3b")))
        painter.drawRoundedRect(wh_rect, 16, 16)

        wh_font = QFont("Segoe UI", 24)
        wh_font.setBold(True)
        painter.setFont(wh_font)
        painter.setPen(QPen(QColor("#4ade80")))
        painter.drawText(QRectF(1450, 335, 380, 45), int(Qt.AlignmentFlag.AlignCenter), "⚡ GITHUB WEBHOOK")

        wh_desc = QFont("Segoe UI", 18)
        painter.setFont(wh_desc)
        painter.setPen(QPen(QColor("#f0fdf4")))
        painter.drawText(
            QRectF(1470, 395, 340, 140),
            int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap),
            "POST /github-webhook\nTriggers Jenkins CI/CD\nAutomated Build & Test",
        )

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target

    def generate_docker_diagram(self, output_path: str | Path) -> Path:
        """Diagram 4: Docker Container Isolation Architecture."""
        image, painter = self._create_base_canvas(
            "Pillar 3: Docker & Containerization",
            "Eliminating 'works on my machine' with standardized, isolated container runtimes",
        )

        # Host Box
        host_rect = QRectF(140, 220, 1640, 760)
        painter.setPen(QPen(QColor("#0284c7"), 3))
        painter.setBrush(QBrush(QColor("#0b1329")))
        painter.drawRoundedRect(host_rect, 18, 18)

        # Host Title
        h_font = QFont("Segoe UI", 26)
        h_font.setBold(True)
        painter.setFont(h_font)
        painter.setPen(QPen(QColor("#38bdf8")))
        painter.drawText(QRectF(170, 245, 800, 40), int(Qt.AlignmentFlag.AlignLeft), "HOST OPERATING SYSTEM / LINUX KERNEL")

        # Docker Engine bar
        eng_rect = QRectF(180, 310, 1560, 90)
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        painter.setBrush(QBrush(QColor("#0369a1")))
        painter.drawRoundedRect(eng_rect, 12, 12)
        eng_font = QFont("Segoe UI", 24)
        eng_font.setBold(True)
        painter.setFont(eng_font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(eng_rect, int(Qt.AlignmentFlag.AlignCenter), "🐳 DOCKER ENGINE (CONTAINER RUNTIME & NETWORKING)")

        # 3 Containers
        containers = [
            ("Frontend Container", "React 19 / Nginx", "Port: 80 -> 3000", "#10b981"),
            ("Backend API Container", "Node.js 22 / Express", "Port: 8080 -> 8080", "#6366f1"),
            ("Database Container", "PostgreSQL 17", "Volume: /var/lib/postgresql", "#f59e0b"),
        ]

        c_w = 480
        c_h = 440
        c_gap = 60
        c_start_x = 180
        c_start_y = 450

        for idx, (c_name, stack, mapping, col_hex) in enumerate(containers):
            cx = c_start_x + idx * (c_w + c_gap)
            box_rect = QRectF(cx, c_start_y, c_w, c_h)

            painter.setPen(QPen(QColor(col_hex), 2))
            painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
            painter.drawRoundedRect(box_rect, 16, 16)

            # Header
            header_r = QRectF(cx, c_start_y, c_w, 80)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(col_hex)))
            painter.drawRoundedRect(header_r, 16, 16)
            painter.drawRect(QRectF(cx, c_start_y + 60, c_w, 20))

            b_font = QFont("Segoe UI", 22)
            b_font.setBold(True)
            painter.setFont(b_font)
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(header_r, int(Qt.AlignmentFlag.AlignCenter), c_name)

            # Details
            st_font = QFont("Segoe UI", 20)
            st_font.setBold(True)
            painter.setFont(st_font)
            painter.setPen(QPen(QColor(col_hex)))
            painter.drawText(QRectF(cx + 20, c_start_y + 120, c_w - 40, 40), int(Qt.AlignmentFlag.AlignCenter), stack)

            m_font = QFont("Consolas", 18)
            painter.setFont(m_font)
            painter.setPen(QPen(QColor("#cbd5e1")))
            painter.drawText(QRectF(cx + 20, c_start_y + 190, c_w - 40, 150), int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap), mapping)

            # Isolated Badge
            iso_rect = QRectF(cx + 60, c_start_y + 360, c_w - 120, 45)
            painter.setPen(QPen(QColor(col_hex), 2))
            painter.setBrush(QBrush(QColor(col_hex).darker(250)))
            painter.drawRoundedRect(iso_rect, 8, 8)
            iso_font = QFont("Segoe UI", 16)
            iso_font.setBold(True)
            painter.setFont(iso_font)
            painter.setPen(QPen(QColor("#f8fafc")))
            painter.drawText(iso_rect, int(Qt.AlignmentFlag.AlignCenter), "✓ Isolated Environment")

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target

    def generate_jenkins_diagram(self, output_path: str | Path) -> Path:
        """Diagram 5: Jenkins CI/CD Pipeline Automation."""
        image, painter = self._create_base_canvas(
            "Pillar 4: Jenkins CI/CD Automation Pipeline",
            "Continuous Integration & Continuous Deployment automated stages",
        )

        stages = [
            ("1. Checkout", "Git Clone", "Fetch latest commit\nfrom main branch", "#38bdf8"),
            ("2. Test", "Run Unit Tests", "Jest & PyTest\nCatch bugs early", "#10b981"),
            ("3. Build", "Docker Image", "Bake application &\ndependencies", "#6366f1"),
            ("4. Security", "Vulnerability Scan", "Scan container layers\nfor CVE exploits", "#f59e0b"),
            ("5. Deploy", "Push to AWS", "Update live EC2/\nECS instances", "#ec4899"),
        ]

        s_w = 300
        s_h = 440
        s_gap = 55
        start_x = 90
        start_y = 300

        for i, (title, action, details, color_hex) in enumerate(stages):
            x = start_x + i * (s_w + s_gap)
            card = QRectF(x, start_y, s_w, s_h)

            painter.setPen(QPen(QColor(color_hex), 2))
            painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
            painter.drawRoundedRect(card, 16, 16)

            # Stage number circle
            circ_center = QPointF(x + s_w / 2, start_y + 60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.drawEllipse(circ_center, 32, 32)
            c_font = QFont("Segoe UI", 22)
            c_font.setBold(True)
            painter.setFont(c_font)
            painter.setPen(QPen(QColor("#0f172a")))
            painter.drawText(QRectF(x, start_y + 35, s_w, 50), int(Qt.AlignmentFlag.AlignCenter), str(i + 1))

            # Title
            t_font = QFont("Segoe UI", 22)
            t_font.setBold(True)
            painter.setFont(t_font)
            painter.setPen(QPen(QColor("#f8fafc")))
            painter.drawText(QRectF(x + 10, start_y + 115, s_w - 20, 40), int(Qt.AlignmentFlag.AlignCenter), title)

            # Action
            a_font = QFont("Segoe UI", 18)
            a_font.setBold(True)
            painter.setFont(a_font)
            painter.setPen(QPen(QColor(color_hex)))
            painter.drawText(QRectF(x + 10, start_y + 165, s_w - 20, 35), int(Qt.AlignmentFlag.AlignCenter), action)

            # Details
            d_font = QFont("Segoe UI", 16)
            painter.setFont(d_font)
            painter.setPen(QPen(QColor("#94a3b8")))
            painter.drawText(QRectF(x + 15, start_y + 225, s_w - 30, 120), int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap), details)

            # Status pill
            pill = QRectF(x + 50, start_y + 360, s_w - 100, 40)
            painter.setPen(QPen(QColor(color_hex), 1))
            painter.setBrush(QBrush(QColor(color_hex).darker(300)))
            painter.drawRoundedRect(pill, 8, 8)
            p_font = QFont("Segoe UI", 15)
            p_font.setBold(True)
            painter.setFont(p_font)
            painter.setPen(QPen(QColor(color_hex)))
            painter.drawText(pill, int(Qt.AlignmentFlag.AlignCenter), "✓ SUCCESS")

            # Arrow between stages
            if i < len(stages) - 1:
                arrow_x = x + s_w + 12
                arrow_y = start_y + s_h / 2
                painter.setPen(QPen(QColor("#64748b"), 4))
                painter.drawLine(arrow_x, arrow_y, arrow_x + 30, arrow_y)

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target

    def generate_aws_diagram(self, output_path: str | Path) -> Path:
        """Diagram 6: AWS Cloud Architecture Topology."""
        image, painter = self._create_base_canvas(
            "Pillar 5: AWS Cloud Infrastructure",
            "Essential entry-level AWS services: VPC, EC2, S3, IAM, and Security",
        )

        # Region Border
        reg_rect = QRectF(140, 220, 1640, 760)
        painter.setPen(QPen(QColor("#f59e0b"), 3))
        painter.setBrush(QBrush(QColor("#0a0f1d")))
        painter.drawRoundedRect(reg_rect, 18, 18)

        # Region Title
        r_font = QFont("Segoe UI", 24)
        r_font.setBold(True)
        painter.setFont(r_font)
        painter.setPen(QPen(QColor("#fbbf24")))
        painter.drawText(QRectF(170, 245, 800, 40), int(Qt.AlignmentFlag.AlignLeft), "☁ AWS REGION (ap-south-1 Mumbai) / CUSTOM VPC")

        # Public Subnet
        pub_rect = QRectF(180, 310, 720, 620)
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(pub_rect, 14, 14)
        pub_font = QFont("Segoe UI", 22)
        pub_font.setBold(True)
        painter.setFont(pub_font)
        painter.setPen(QPen(QColor("#38bdf8")))
        painter.drawText(QRectF(205, 330, 400, 35), int(Qt.AlignmentFlag.AlignLeft), "PUBLIC SUBNET (INTERNET FACING)")

        # EC2 inside Public Subnet
        ec2_rect = QRectF(220, 390, 640, 220)
        painter.setPen(QPen(QColor("#f97316"), 2))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(ec2_rect, 12, 12)
        ec2_font = QFont("Segoe UI", 20)
        ec2_font.setBold(True)
        painter.setFont(ec2_font)
        painter.setPen(QPen(QColor("#fb923c")))
        painter.drawText(QRectF(245, 410, 500, 35), int(Qt.AlignmentFlag.AlignLeft), "🖥 AMAZON EC2 VIRTUAL SERVER")
        d_font = QFont("Consolas", 18)
        painter.setFont(d_font)
        painter.setPen(QPen(QColor("#f8fafc")))
        painter.drawText(
            QRectF(245, 460, 590, 130),
            int(Qt.AlignmentFlag.AlignLeft) | int(Qt.TextFlag.TextWordWrap),
            "Instance: t2.micro / t3.micro (Ubuntu 24.04)\nRuns: Docker Engine & Jenkins Build Agent\nSecurity Group: Ports 22 (SSH), 80 (HTTP), 443 (HTTPS)",
        )

        # IAM & Billing Alert inside Public Subnet
        iam_rect = QRectF(220, 650, 640, 240)
        painter.setPen(QPen(QColor("#ef4444"), 2))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(iam_rect, 12, 12)
        iam_font = QFont("Segoe UI", 20)
        iam_font.setBold(True)
        painter.setFont(iam_font)
        painter.setPen(QPen(QColor("#f87171")))
        painter.drawText(QRectF(245, 670, 500, 35), int(Qt.AlignmentFlag.AlignLeft), "🛡 AWS IAM & CLOUDWATCH ALERTS")
        painter.setFont(d_font)
        painter.setPen(QPen(QColor("#f8fafc")))
        painter.drawText(
            QRectF(245, 720, 590, 140),
            int(Qt.AlignmentFlag.AlignLeft) | int(Qt.TextFlag.TextWordWrap),
            "IAM Role: Least-privilege access for EC2\nBilling Alert: $1 threshold email notification\nPrevents accidental free-tier overages",
        )

        # Private Subnet
        priv_rect = QRectF(960, 310, 780, 620)
        painter.setPen(QPen(QColor("#10b981"), 2))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(priv_rect, 14, 14)
        priv_font = QFont("Segoe UI", 22)
        priv_font.setBold(True)
        painter.setFont(priv_font)
        painter.setPen(QPen(QColor("#34d399")))
        painter.drawText(QRectF(985, 330, 500, 35), int(Qt.AlignmentFlag.AlignLeft), "PRIVATE STORAGE & REGISTRY")

        # S3 Bucket
        s3_rect = QRectF(1000, 390, 700, 240)
        painter.setPen(QPen(QColor("#10b981"), 2))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(s3_rect, 12, 12)
        s3_font = QFont("Segoe UI", 20)
        s3_font.setBold(True)
        painter.setFont(s3_font)
        painter.setPen(QPen(QColor("#34d399")))
        painter.drawText(QRectF(1025, 410, 500, 35), int(Qt.AlignmentFlag.AlignLeft), "🪣 AMAZON S3 OBJECT STORAGE")
        painter.setFont(d_font)
        painter.setPen(QPen(QColor("#f8fafc")))
        painter.drawText(
            QRectF(1025, 460, 650, 140),
            int(Qt.AlignmentFlag.AlignLeft) | int(Qt.TextFlag.TextWordWrap),
            "Encrypted Storage: AES-256 server-side\nStores: Database backups, build artifacts, static web assets\nLifecycle Rules: Auto-archive old logs",
        )

        # ECR Container Registry
        ecr_rect = QRectF(1000, 670, 700, 220)
        painter.setPen(QPen(QColor("#a855f7"), 2))
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(ecr_rect, 12, 12)
        ecr_font = QFont("Segoe UI", 20)
        ecr_font.setBold(True)
        painter.setFont(ecr_font)
        painter.setPen(QPen(QColor("#c084fc")))
        painter.drawText(QRectF(1025, 690, 500, 35), int(Qt.AlignmentFlag.AlignLeft), "📦 AMAZON ECR (CONTAINER REGISTRY)")
        painter.setFont(d_font)
        painter.setPen(QPen(QColor("#f8fafc")))
        painter.drawText(
            QRectF(1025, 740, 650, 130),
            int(Qt.AlignmentFlag.AlignLeft) | int(Qt.TextFlag.TextWordWrap),
            "Secure Docker image repository\nAutomated vulnerability scanning on push\nDirect pull integration with EC2 and ECS",
        )

        painter.end()
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(target), "PNG")
        return target


def generate_all_devops_diagrams(output_dir: str | Path) -> dict[str, Path]:
    """Generates all 5 standard DevOps diagrams and returns mapping of diagram_type -> Path."""
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generator = DevOpsDiagramGenerator()

    mapping = {
        "pillars_overview": generator.generate_pillars_overview(out / "pillars_overview.png"),
        "devops_flow": generator.generate_pillars_overview(out / "devops_flow.png"),
        "terminal": generator.generate_terminal_diagram(out / "terminal.png"),
        "git_tree": generator.generate_git_diagram(out / "git_tree.png"),
        "docker": generator.generate_docker_diagram(out / "docker.png"),
        "jenkins": generator.generate_jenkins_diagram(out / "jenkins.png"),
        "aws": generator.generate_aws_diagram(out / "aws.png"),
        "roadmap": generator.generate_pillars_overview(out / "roadmap.png"),
    }
    return mapping
