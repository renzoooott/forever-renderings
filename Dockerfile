FROM rust:latest as rust-builder

# Install ntsc-rs dependencies including gstreamer and GTK
RUN apt-get update && apt-get install -y \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libgtk-3-dev \
    libatk1.0-dev \
    libclang1 \
    libclang-dev \
    clang \
    && rm -rf /var/lib/apt/lists/*

# Clone and build ntsc-rs
RUN git clone --recurse-submodules https://github.com/valadaptive/ntsc-rs.git /ntsc-rs
WORKDIR /ntsc-rs
RUN cargo build --release

FROM python:3.11-slim

# Install FFmpeg, GTK3, and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libgtk-3-0 \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-alsa \
    gstreamer1.0-pulseaudio \
    gstreamer1.0-x \
    gstreamer1.0-gl \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GStreamer
ENV GST_DEBUG=3
ENV RUST_BACKTRACE=1

# Copy ntsc-rs from builder
COPY --from=rust-builder /ntsc-rs/target/release/ntsc-rs-cli /usr/local/bin/

# Set up app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create upload and processed directories
RUN mkdir -p uploads processed

# Expose the port
EXPOSE 5001

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "server:app"]
