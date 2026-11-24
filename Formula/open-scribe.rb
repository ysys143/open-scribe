class OpenScribe < Formula
  desc "Transcribe and summarize audio or YouTube with explicit JSON settings"
  homepage "https://github.com/ysys143/open-scribe"
  url "https://github.com/ysys143/open-scribe/releases/download/0.3.2/open-scribe-0.3.2.tar.gz"
  version "0.3.2"
  sha256 "09accc431ac87c2b6d079b0523a4847e351c22cf4a249dfadf808b390a26e9b0"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv"
  depends_on "ffmpeg"

  preserve_rpath

  def install
    libexec.install "src", "bot", "main.py", "requirements.txt", "requirements.cloud.txt", "settings.example.json"
    system Formula["uv"].opt_bin/"uv", "venv", "--python", Formula["python@3.11"].opt_bin/"python3.11", libexec/".venv"
    system Formula["uv"].opt_bin/"uv", "pip", "install", "--python", libexec/".venv/bin/python", "-r", libexec/"requirements.txt"
    (bin/"scribe").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/.venv/bin/python" -B "#{libexec}/main.py" "$@"
    EOS
    (bin/"scribe").chmod 0755
    (bin/"scr").make_symlink "scribe"
    (bin/"openscribe").make_symlink "scribe"
  end

  def caveats
    <<~EOS
      General settings: ~/.config/open-scribe/settings.json
      Inspect with: scr config show
      Validate with: scr config validate
      Legacy .env option defaults are no longer loaded.
      Set copy_to_path explicitly and reference existing credential files in JSON.
      Example: #{libexec}/settings.example.json
    EOS
  end

  test do
    ENV["OPEN_SCRIBE_SETTINGS"] = (testpath/"settings.json").to_s
    (testpath/"settings.json").write '{"copy_to_path":null}'
    assert_match "0.3.2", shell_output("#{bin}/scribe --version")
    system bin/"openscribe", "config", "validate"
    assert_match "저장된 녹취가 없습니다", shell_output("#{bin}/scr ls")
  end
end
