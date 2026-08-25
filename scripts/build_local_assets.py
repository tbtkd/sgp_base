"""Genera la capa local de utilidades e iconos usada por las plantillas.

No descarga recursos. El resultado es determinista y se empaqueta con la app,
por lo que la interfaz no depende de Tailwind, fuentes o iconos servidos por CDN.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTILITY_TARGET = ROOT / "app" / "static" / "css" / "utilities.css"
ICON_TARGET = ROOT / "app" / "static" / "css" / "icons.css"

COLORS = {
    "black": "#000000",
    "white": "#ffffff",
    "gray-50": "#f9fafb",
    "gray-100": "#f3f4f6",
    "gray-200": "#e5e7eb",
    "gray-300": "#d1d5db",
    "gray-400": "#9ca3af",
    "gray-500": "#6b7280",
    "gray-600": "#4b5563",
    "gray-700": "#374151",
    "gray-800": "#1f2937",
    "gray-900": "#111827",
    "slate-50": "#f8fafc",
    "slate-100": "#f1f5f9",
    "slate-200": "#e2e8f0",
    "slate-300": "#cbd5e1",
    "slate-400": "#94a3b8",
    "slate-500": "#64748b",
    "slate-600": "#475569",
    "slate-700": "#334155",
    "slate-800": "#1e293b",
    "slate-900": "#0f172a",
    "red-50": "#fef2f2",
    "red-100": "#fee2e2",
    "red-200": "#fecaca",
    "red-600": "#dc2626",
    "red-700": "#b91c1c",
    "red-800": "#991b1b",
    "red-900": "#7f1d1d",
    "rose-50": "#fff1f2",
    "rose-200": "#fecdd3",
    "rose-700": "#be123c",
    "amber-50": "#fffbeb",
    "amber-100": "#fef3c7",
    "amber-200": "#fde68a",
    "amber-300": "#fcd34d",
    "amber-500": "#f59e0b",
    "amber-600": "#d97706",
    "amber-700": "#b45309",
    "amber-800": "#92400e",
    "amber-900": "#78350f",
    "blue-50": "#eff6ff",
    "blue-100": "#dbeafe",
    "blue-200": "#bfdbfe",
    "blue-600": "#2563eb",
    "blue-700": "#1d4ed8",
    "blue-800": "#1e40af",
    "blue-900": "#1e3a8a",
    "emerald-50": "#ecfdf5",
    "emerald-100": "#d1fae5",
    "emerald-200": "#a7f3d0",
    "emerald-500": "#10b981",
    "emerald-600": "#059669",
    "emerald-700": "#047857",
    "emerald-800": "#065f46",
    "teal-50": "#f0fdfa",
    "teal-100": "#ccfbf1",
    "teal-200": "#99f6e4",
    "teal-500": "#14b8a6",
    "teal-600": "#0d9488",
    "teal-700": "#0f766e",
    "teal-800": "#115e59",
    "teal-900": "#134e4a",
}

SPACING = {
    "0": "0",
    "0.5": "0.125rem",
    "1": "0.25rem",
    "1.5": "0.375rem",
    "2": "0.5rem",
    "2.5": "0.625rem",
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "7": "1.75rem",
    "8": "2rem",
    "10": "2.5rem",
    "11": "2.75rem",
    "12": "3rem",
    "14": "3.5rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem",
    "36": "9rem",
}

BREAKPOINTS = {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"}


def _escape(value: str) -> str:
    return re.sub(r"([^a-zA-Z0-9_-])", lambda match: "\\" + match.group(1), value)


def _rgba(hex_color: str, opacity: float) -> str:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return f"rgb({red} {green} {blue} / {opacity:g})"


def _color_value(value: str) -> str | None:
    name, separator, opacity = value.partition("/")
    color = COLORS.get(name)
    if not color:
        return None
    return _rgba(color, int(opacity) / 100) if separator and opacity.isdigit() else color


def _arbitrary(value: str) -> str | None:
    if value.startswith("[") and value.endswith("]"):
        return value[1:-1].replace("_", " ")
    return None


def _base_declarations(token: str) -> str | None:  # noqa: C901
    static = {
        "block": "display:block",
        "inline": "display:inline",
        "inline-block": "display:inline-block",
        "inline-flex": "display:inline-flex",
        "flex": "display:flex",
        "grid": "display:grid",
        "hidden": "display:none",
        "fixed": "position:fixed",
        "absolute": "position:absolute",
        "relative": "position:relative",
        "sticky": "position:sticky",
        "inset-0": "inset:0",
        "items-start": "align-items:flex-start",
        "items-center": "align-items:center",
        "items-end": "align-items:flex-end",
        "justify-start": "justify-content:flex-start",
        "justify-center": "justify-content:center",
        "justify-between": "justify-content:space-between",
        "justify-end": "justify-content:flex-end",
        "flex-1": "flex:1 1 0%",
        "flex-grow": "flex-grow:1",
        "flex-none": "flex:none",
        "shrink-0": "flex-shrink:0",
        "flex-col": "flex-direction:column",
        "flex-row": "flex-direction:row",
        "flex-wrap": "flex-wrap:wrap",
        "grid-flow-col": "grid-auto-flow:column",
        "col-span-full": "grid-column:1 / -1",
        "w-full": "width:100%",
        "w-auto": "width:auto",
        "h-full": "height:100%",
        "min-w-0": "min-width:0",
        "min-h-0": "min-height:0",
        "min-h-full": "min-height:100%",
        "min-h-screen": "min-height:100vh",
        "max-w-none": "max-width:none",
        "overflow-hidden": "overflow:hidden",
        "overflow-auto": "overflow:auto",
        "overflow-x-auto": "overflow-x:auto",
        "overflow-y-auto": "overflow-y:auto",
        "resize-y": "resize:vertical",
        "border-collapse": "border-collapse:collapse",
        "break-all": "word-break:break-all",
        "truncate": "overflow:hidden;text-overflow:ellipsis;white-space:nowrap",
        "whitespace-nowrap": "white-space:nowrap",
        "whitespace-pre-line": "white-space:pre-line",
        "text-left": "text-align:left",
        "text-center": "text-align:center",
        "text-right": "text-align:right",
        "uppercase": "text-transform:uppercase",
        "capitalize": "text-transform:capitalize",
        "italic": "font-style:italic",
        "font-normal": "font-weight:400",
        "font-medium": "font-weight:500",
        "font-semibold": "font-weight:600",
        "font-bold": "font-weight:700",
        "font-black": "font-weight:900",
        "fw-bold": "font-weight:700",
        "font-sans": "font-family:Inter,Segoe UI,Arial,sans-serif",
        "font-mono": "font-family:ui-monospace,SFMono-Regular,Consolas,monospace",
        "antialiased": "-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale",
        "leading-none": "line-height:1",
        "leading-tight": "line-height:1.25",
        "leading-relaxed": "line-height:1.625",
        "tracking-wide": "letter-spacing:.025em",
        "tracking-wider": "letter-spacing:.05em",
        "cursor-pointer": "cursor:pointer",
        "cursor-wait": "cursor:wait",
        "pointer-events-none": "pointer-events:none",
        "select-none": "user-select:none",
        "list-none": "list-style:none",
        "appearance-none": "appearance:none",
        "object-cover": "object-fit:cover",
        "object-contain": "object-fit:contain",
        "transition": "transition-property:color,background-color,border-color,opacity,box-shadow,transform;transition-duration:.15s",
        "transition-all": "transition-property:all;transition-duration:.15s",
        "transition-colors": "transition-property:color,background-color,border-color;transition-duration:.15s",
        "transition-opacity": "transition-property:opacity;transition-duration:.15s",
        "transform": "transform:translate(var(--tw-translate-x,0),var(--tw-translate-y,0))",
        "shadow": "box-shadow:0 1px 3px rgb(15 23 42 / .12)",
        "shadow-sm": "box-shadow:0 1px 2px rgb(15 23 42 / .08)",
        "shadow-md": "box-shadow:0 4px 8px rgb(15 23 42 / .12)",
        "shadow-lg": "box-shadow:0 10px 20px rgb(15 23 42 / .14)",
        "shadow-xl": "box-shadow:0 20px 30px rgb(15 23 42 / .16)",
        "shadow-2xl": "box-shadow:0 25px 50px rgb(15 23 42 / .22)",
        "shadow-none": "box-shadow:none",
        "ring-0": "box-shadow:none",
        "ring-teal-500": "box-shadow:0 0 0 3px rgb(20 184 166 / .35)",
        "ring-emerald-500": "box-shadow:0 0 0 3px rgb(16 185 129 / .35)",
        "mx-auto": "margin-left:auto;margin-right:auto",
        "ml-auto": "margin-left:auto",
        "me-2": "margin-inline-end:.5rem",
        "sr-only": "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0",
        "container": "width:100%;margin-left:auto;margin-right:auto",
        "display-4": "font-size:3rem;line-height:1",
        "text-muted": "color:#64748b",
        "text-warning": "color:#d97706",
        "text-current": "color:currentColor",
        "bg-opacity-50": "background-color:rgb(0 0 0 / .5)",
        "backdrop-blur-sm": "backdrop-filter:blur(4px)",
        "outline-none": "outline:2px solid transparent;outline-offset:2px",
    }
    if token in static:
        return static[token]

    match = re.fullmatch(r"grid-cols-(\d+)", token)
    if match:
        return f"grid-template-columns:repeat({match.group(1)},minmax(0,1fr))"
    match = re.fullmatch(r"col-span-(\d+)", token)
    if match:
        return f"grid-column:span {match.group(1)} / span {match.group(1)}"

    match = re.fullmatch(r"(?:z|opacity|duration)-(\d+)", token)
    if match:
        prefix = token.split("-", 1)[0]
        value = int(match.group(1))
        return {"z": f"z-index:{value}", "opacity": f"opacity:{value / 100:g}", "duration": f"transition-duration:{value}ms"}[prefix]

    match = re.fullmatch(r"(m|p)([trblxy]?)-(.+)", token)
    if match and match.group(3) in SPACING:
        kind, axis, raw = match.groups()
        prop = "margin" if kind == "m" else "padding"
        value = SPACING[raw]
        suffixes = {
            "": [""], "t": ["-top"], "r": ["-right"], "b": ["-bottom"], "l": ["-left"],
            "x": ["-left", "-right"], "y": ["-top", "-bottom"],
        }[axis]
        return ";".join(f"{prop}{suffix}:{value}" for suffix in suffixes)
    match = re.fullmatch(r"-?(m[trbl]?)-(.+)", token)
    if match and match.group(2) in SPACING:
        axis, raw = match.groups()
        suffix = {"m": "", "mt": "-top", "mr": "-right", "mb": "-bottom", "ml": "-left"}[axis]
        value = SPACING[raw]
        if token.startswith("-"):
            value = "-" + value
        return f"margin{suffix}:{value}"
    match = re.fullmatch(r"gap(?:-([xy]))?-(.+)", token)
    if match and match.group(2) in SPACING:
        prop = {None: "gap", "x": "column-gap", "y": "row-gap"}[match.group(1)]
        return f"{prop}:{SPACING[match.group(2)]}"

    match = re.fullmatch(r"(w|h|min-w|min-h|max-w|max-h)-(.+)", token)
    if match:
        prefix, raw = match.groups()
        prop = {"w": "width", "h": "height", "min-w": "min-width", "min-h": "min-height", "max-w": "max-width", "max-h": "max-height"}[prefix]
        named = {
            "xs": "20rem", "sm": "24rem", "md": "28rem", "lg": "32rem", "xl": "36rem", "2xl": "42rem",
            "3xl": "48rem", "4xl": "56rem", "5xl": "64rem", "6xl": "72rem", "7xl": "80rem", "screen": "100vh",
        }
        value = SPACING.get(raw) or named.get(raw) or _arbitrary(raw)
        if value:
            return f"{prop}:{value}"

    match = re.fullmatch(r"(top|right|bottom|left)-(.+)", token)
    if match:
        value = SPACING.get(match.group(2)) or ({"1/2": "50%"}.get(match.group(2))) or _arbitrary(match.group(2))
        if value:
            return f"{match.group(1)}:{value}"
    match = re.fullmatch(r"-(top|right|bottom|left)-(.+)", token)
    if match and match.group(2) in SPACING:
        return f"{match.group(1)}:-{SPACING[match.group(2)]}"

    match = re.fullmatch(r"text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)", token)
    if match:
        sizes = {"xs": ".75rem", "sm": ".875rem", "base": "1rem", "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem", "6xl": "3.75rem"}
        return f"font-size:{sizes[match.group(1)]}"
    match = re.fullmatch(r"text-\[(.+)\]", token)
    if match:
        return f"font-size:{match.group(1)}"
    for prefix, prop in (("text-", "color"), ("bg-", "background-color"), ("border-", "border-color")):
        if token.startswith(prefix):
            color = _color_value(token[len(prefix) :])
            if color:
                return f"{prop}:{color}"

    if token == "border":
        return "border-width:1px;border-style:solid"
    if token == "border-0":
        return "border-width:0"
    if token == "border-2":
        return "border-width:2px;border-style:solid"
    if token in {"border-t", "border-b", "border-l", "border-r"}:
        return f"border-{token[-1].translate(str.maketrans({'t':'top','b':'bottom','l':'left','r':'right'}))}-width:1px"
    rounded = {
        "rounded": ".25rem", "rounded-md": ".375rem", "rounded-lg": ".5rem", "rounded-xl": ".75rem",
        "rounded-2xl": "1rem", "rounded-3xl": "1.5rem", "rounded-full": "9999px", "rounded-none": "0",
    }
    if token in rounded:
        return f"border-radius:{rounded[token]}"

    match = re.fullmatch(r"ring-(\d+)", token)
    if match:
        return f"box-shadow:0 0 0 {match.group(1)}px rgb(20 184 166 / .35)"
    match = re.fullmatch(r"translate-([xy])-(.+)", token)
    if match:
        value = SPACING.get(match.group(2)) or ("50%" if match.group(2) == "1/2" else None)
        if value:
            return f"--tw-translate-{match.group(1)}:{value};transform:translate(var(--tw-translate-x,0),var(--tw-translate-y,0))"
    match = re.fullmatch(r"-translate-([xy])-(.+)", token)
    if match:
        value = SPACING.get(match.group(2)) or ("50%" if match.group(2) == "1/2" else None)
        if value:
            return f"--tw-translate-{match.group(1)}:-{value};transform:translate(var(--tw-translate-x,0),var(--tw-translate-y,0))"
    return None


def _extract_classes() -> set[str]:
    tokens: set[str] = set()
    for template in (ROOT / "app" / "templates").rglob("*.html"):
        content = template.read_text(encoding="utf-8")
        content = re.sub(r"{[%{].*?[%}]}", " ", content, flags=re.DOTALL)
        for match in re.finditer(r'class\s*=\s*["\']([^"\']*)["\']', content, flags=re.DOTALL):
            tokens.update(part for part in match.group(1).split() if part)
    return tokens


def _compile_rule(token: str) -> tuple[str, str] | None:
    parts = token.split(":")
    base = parts.pop()
    declarations = _base_declarations(base)
    if not declarations:
        return None
    selector = f".{_escape(token)}"
    media = None
    pseudo_element = ""
    for variant in parts:
        if variant in BREAKPOINTS:
            media = BREAKPOINTS[variant]
        elif variant in {"hover", "focus", "focus-visible", "active", "disabled", "checked"}:
            selector += f":{variant}"
        elif variant == "file":
            selector += "::file-selector-button"
        elif variant == "before":
            pseudo_element = "::before"
            declarations = "content:'';" + declarations
        elif variant == "group-hover":
            selector = f".group:hover {selector}"
        else:
            return None
    rule = f"{selector}{pseudo_element}{{{declarations}}}"
    return (media or "", rule)


def build_utilities() -> str:
    rules: list[tuple[str, str]] = []
    for token in sorted(_extract_classes()):
        compiled = _compile_rule(token)
        if compiled:
            rules.append(compiled)
    plain = [rule for media, rule in rules if not media]
    responsive = []
    for breakpoint in BREAKPOINTS.values():
        grouped = [rule for media, rule in rules if media == breakpoint]
        if grouped:
            responsive.append(f"@media (min-width:{breakpoint}){{{''.join(grouped)}}}")
    extras = [
        "*,::before,::after{box-sizing:border-box;border-color:#e5e7eb}",
        "html,body{margin:0;min-height:100%}",
        "button,input,select,textarea{font:inherit}",
        ".space-x-2>*+*{margin-left:.5rem}.space-y-1>*+*{margin-top:.25rem}.space-y-2>*+*{margin-top:.5rem}.space-y-3>*+*{margin-top:.75rem}.space-y-4>*+*{margin-top:1rem}.space-y-5>*+*{margin-top:1.25rem}.space-y-6>*+*{margin-top:1.5rem}.space-y-8>*+*{margin-top:2rem}",
        ".divide-y>*+*{border-top-width:1px}.divide-gray-100>*+*{border-color:#f3f4f6}",
        "[hidden]{display:none!important}.modal-open{overflow:hidden}",
    ]
    return "/* Generado por scripts/build_local_assets.py. */\n" + "\n".join(extras + plain + responsive) + "\n"


ICON_GLYPHS = {
    "allergies": "⚠", "arrow-left": "←", "arrow-up-right-from-square": "↗", "ban": "⊘", "bars": "☰",
    "bell": "●", "bell-slash": "○", "boxes": "▦", "calendar-alt": "▣", "calendar-check": "✓", "calendar-plus": "+",
    "chart-bar": "▥", "chart-pie": "◕", "check-circle": "✓", "chevron-down": "⌄", "chevron-left": "‹",
    "chevron-right": "›", "circle-info": "i", "circle-notch": "◌", "clinic-medical": "+", "clipboard-list": "☷",
    "clock": "◷", "cog": "⚙", "edit": "✎", "ellipsis-v": "⋮", "exclamation-circle": "!", "eye": "◉",
    "file-csv": "CSV", "file-excel": "XLS", "file-invoice-dollar": "$", "file-medical": "▤", "filter": "▽",
    "flask": "⚗", "home": "⌂", "key": "⚿", "list": "☷", "magnifying-glass-dollar": "$", "money-bill-wave": "$",
    "moon": "☾", "notes-medical": "▤", "pencil-alt": "✎", "person-running": "↗", "plus": "+", "prescription": "Rx",
    "print": "▣", "receipt": "▤", "running": "↗", "search": "⌕", "shield-alt": "◆", "sign-out-alt": "↪",
    "sliders-h": "☷", "sort": "↕", "sort-down": "↓", "sort-up": "↑", "stethoscope": "+", "times": "×",
    "trash-alt": "⌫", "triangle-exclamation": "!", "user": "●", "user-check": "✓", "user-circle": "●",
    "user-injured": "+", "user-md": "+", "user-plus": "+", "user-times": "×", "users": "●●", "users-cog": "⚙",
    "utensils": "⋔", "weight": "▰", "whatsapp": "☎", "database": "▤", "download": "↓",
}


def build_icons() -> str:
    lines = [
        "/* Iconografía local sin fuentes externas. */",
        ".fas,.far,.fab{display:inline-flex;min-width:1em;align-items:center;justify-content:center;font-family:Segoe UI Symbol,Arial,sans-serif;font-style:normal;font-weight:700;line-height:1;text-align:center}",
        ".fa-spin{animation:sgpn-icon-spin 1s linear infinite}@keyframes sgpn-icon-spin{to{transform:rotate(360deg)}}",
    ]
    lines.extend(f'.fa-{name}::before{{content:"{glyph}"}}' for name, glyph in ICON_GLYPHS.items())
    return "\n".join(lines) + "\n"


def _write_or_check(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if check:
        return current == content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Falla si los archivos generados no están actualizados.")
    args = parser.parse_args()
    results = (
        _write_or_check(UTILITY_TARGET, build_utilities(), args.check),
        _write_or_check(ICON_TARGET, build_icons(), args.check),
    )
    if not all(results):
        print("Los recursos locales generados no están actualizados.")
        return 1
    if not args.check:
        print(f"Generados: {UTILITY_TARGET.relative_to(ROOT)}, {ICON_TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
