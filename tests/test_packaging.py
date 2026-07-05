from pathlib import Path

import pytest

from causal_uplift_experimentation_ops import __version__
from causal_uplift_experimentation_ops.cli import main, project_info

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_version_command_works(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--version"])

    assert error.value.code == 0
    assert f"causal-uplift-ops {__version__}" in capsys.readouterr().out


def test_project_info_command_works(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    assert main(["project-info", "--artifact-directory", str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "Package: causal-uplift-experimentation-ops" in output
    assert "Selected model: logistic_s_learner" in output
    assert "Promotion status: hold" in output
    assert "synthetic data only" in output


def test_project_info_reads_artifact_metadata(tmp_path: Path) -> None:
    (tmp_path / "policy_config.json").write_text(
        '{"model_name":"model-a","policy_name":"policy-b"}',
        encoding="utf-8",
    )
    (tmp_path / "manifest.json").write_text(
        '{"artifact_version":"2.3.4"}',
        encoding="utf-8",
    )

    values = project_info(tmp_path)

    assert values["selected_model"] == "model-a"
    assert values["selected_policy"] == "policy-b"
    assert values["artifact_version"] == "2.3.4"


@pytest.mark.parametrize(
    "relative_path",
    [
        "Makefile",
        "Dockerfile",
        ".dockerignore",
        ".github/workflows/ci.yml",
        "scripts/run_portfolio_smoke.sh",
        "scripts/docker_smoke_test.sh",
        "docs/architecture.md",
        "docs/reproducibility.md",
        "docs/portfolio_review.md",
    ],
)
def test_packaging_file_exists(relative_path: str) -> None:
    assert (PROJECT_ROOT / relative_path).is_file()


def test_makefile_exposes_smoke_target() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "smoke:" in makefile
    assert "check:" in makefile


def test_portfolio_smoke_script_is_executable() -> None:
    script = PROJECT_ROOT / "scripts/run_portfolio_smoke.sh"

    assert script.stat().st_mode & 0o111
