class OpenScribe < Formula
  desc "YouTube video transcription tool with multiple engines"
  homepage "https://github.com/ysys143/open-scribe"
  url "https://github.com/ysys143/open-scribe/archive/refs/tags/0.1.0.tar.gz"
  sha256 "e2fcdb8ae7dc550fbf794df2b7d085d6f99971f389b1843709a18d1372555b93"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv"

  def install
    # Create installation directory
    prefix_dir = libexec

    # Copy project files to libexec
    cp_r ".", prefix_dir

    # Create Python virtual environment
    system "uv", "venv", "#{prefix_dir}/.venv"

    # Install dependencies using uv
    system "#{prefix_dir}/.venv/bin/pip", "install", "--upgrade", "pip", "setuptools", "wheel"
    system "#{prefix_dir}/.venv/bin/uv", "pip", "install", "-r", "#{prefix_dir}/requirements.txt"

    # Create wrapper script
    bin.mkpath
    (bin/"scribe").write <<~EOS
      #!/bin/bash
      export OPEN_SCRIBE_HOME="#{prefix_dir}"
      export PATH="#{prefix_dir}/.local/bin:$PATH"
      source "#{prefix_dir}/.venv/bin/activate"
      exec "#{prefix_dir}/.venv/bin/python" "#{prefix_dir}/main.py" "$@"
    EOS
    (bin/"scribe").chmod 0755
  end

  def post_install
    puts <<~EOS
      ✅ Open-Scribe installed successfully!

      To get started:
        scribe "https://www.youtube.com/watch?v=VIDEO_ID"

      On first run, you'll be prompted for your OpenAI API Key.
      Get your key at: https://platform.openai.com/api-keys

      Options:
        scribe "URL" --engine whisper-api --summary
        scribe "URL" --timestamp --srt
        scribe "PLAYLIST_URL" --parallel 4

      For more help:
        scribe --help
    EOS
  end

  test do
    system "#{bin}/scribe", "--help"
  end
end
