# MediaDetector

MediaDetector is a web-based application for processing video and audio files using AI-powered modules.

The application is designed around a simple project-based workflow: each project is represented by a directory on the filesystem containing the original media, intermediate files, generated results, metadata, and other artifacts produced during processing.

The project currently targets local or single-server usage and does not require user accounts or a database.

## Goals

The main goals of MediaDetector are:

* Provide a simple web interface for managing media processing projects.
* Support video and audio as input media.
* Store all project-related files directly on the filesystem.
* Allow the output of one processing module to become the input of another.
* Keep AI processing modules independent from the web application.
* Support long-running media processing tasks.
* Provide a foundation for future GPU-accelerated processing.
* Keep the initial architecture simple and easy to develop and maintain.

## Architecture

MediaDetector consists of two main applications:

```text
┌──────────────────────┐
│       Frontend       │
│   React + TypeScript │
│                      │
│      Vite            │
└──────────┬───────────┘
           │
           │ HTTP / JSON
           ▼
┌──────────────────────┐
│       Backend        │
│       FastAPI        │
│        Python        │
└──────────┬───────────┘
           │
           ├───────────────┐
           │               │
           ▼               ▼
     Filesystem       AI Processing
                       Modules
```

### Frontend

The frontend is responsible for:

* Project management UI.
* Uploading media files.
* Displaying project information.
* Starting processing tasks.
* Displaying processing status and results.

Technologies:

* React
* TypeScript
* Vite

### Backend

The backend provides the HTTP API used by the frontend.

It is responsible for:

* Creating and managing projects.
* Validating requests.
* Managing project files.
* Starting and monitoring processing tasks.
* Communicating with processing modules.

Technologies:

* Python
* FastAPI
* Uvicorn

### AI Processing Modules

AI processing is kept separate from the API layer.

A processing module should focus on a specific task, for example:

* Face detection and blurring.
* Speech-to-text transcription.
* Audio processing.
* Object detection.
* Video analysis.
* Other AI-based transformations.

The backend should not need to know how a particular AI model works. It should only be responsible for starting the appropriate processing task and tracking its state.

This separation allows individual modules to be developed and tested independently.

## Project Storage

MediaDetector does not currently use a database.

Projects are stored directly in:

```text
data/
```

Each project has its own directory:

```text
data/
└── Example Project/
    ├── project_info.json
    ├── input_video.mp4
    ├── extracted_audio.wav
    ├── transcription.json
    ├── faces_blurred.mp4
    └── final.mp4
```

The `project_info.json` file contains project metadata, for example:

```json
{
  "name": "Example Project",
  "created_at": "2026-08-30T12:00:00"
}
```

All files generated during processing remain inside the project directory.

This makes a project self-contained and allows the output of one module to be used as the input of another.

For example:

```text
input_video.mp4
       │
       ▼
   Face Blur
       │
       ▼
faces_blurred.mp4
       │
       ▼
  Transcription
       │
       ▼
transcription.json
```

## Processing Model

Media processing can be computationally expensive and may take several minutes or longer for large files.

Long-running tasks should therefore not block an HTTP request.

The intended processing flow is:

```text
User
 │
 │ Start processing
 ▼
Frontend
 │
 │ POST /api/...
 ▼
FastAPI
 │
 │ Create processing task
 ▼
Processor
 │
 ├── Read input files
 ├── Run AI models
 ├── Process media
 └── Write output files
 │
 ▼
Project directory
 │
 ▼
Frontend receives task status
```

The processing architecture is designed so that GPU acceleration can be introduced later without changing the basic project model.

## Current Status

MediaDetector is currently in early development.

### Implemented

* Project structure.
* FastAPI backend.
* React + TypeScript frontend.
* Filesystem-based project storage.
* Project creation.
* Project metadata stored as JSON.
* Project listing through the API.
* Basic frontend/backend communication.

### Planned

* Project detail view.
* Media file upload.
* Media file management.
* Processing task management.
* Processing progress and status.
* AI processing modules.
* Video and audio previews.
* FFmpeg-based media processing.
* Face detection and blurring.
* Speech-to-text transcription.
* GPU acceleration.
* Improved error handling and logging.
* Processing pipelines.

## Development Setup

MediaDetector is currently designed to run directly on the host system without Docker.

The recommended development environment is:

* Windows 11
* Python
* Node.js
* npm

Docker and a database are intentionally not required for the current architecture.

## Running the Backend

Enter the backend directory:

```bash
cd backend
```

Activate the Python virtual environment:

```bash
source .venv/bin/activate
```

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## Running the Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The development frontend will be available at:

```text
http://localhost:5173
```

## Project Structure

The repository currently follows this structure:

```text
MediaDetector/
│
├── backend/
│   ├── .venv/
│   ├── main.py
│   ├── schemas.py
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── data/
│   └── projects/
│
├── .gitignore
└── README.md
```

The `.venv` directory and project media files are intentionally excluded from version control.

## Design Principles

MediaDetector follows several simple principles:

### 1. Files are the source of project data

There is no database dependency for project storage.

### 2. Projects are self-contained

Everything related to a project should live inside its project directory.

### 3. Processing modules are independent

AI modules should not contain web application logic.

### 4. Modules communicate through files

A generated file can be consumed by another module.

### 5. Long-running tasks are asynchronous

Video and audio processing should not keep HTTP requests open for the entire duration of a task.

### 6. Start simple

Additional infrastructure such as databases, message queues, containers, or distributed workers should only be introduced when the application actually requires them.

## Future Architecture

The initial architecture is intentionally simple, but it can evolve if MediaDetector grows.

For example:

```text
                    ┌───────────────┐
                    │    React      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Project Storage        Task Manager
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                           Face AI  Audio AI  Video AI
                              │        │        │
                              └────────┼────────┘
                                       ▼
                              Project Filesystem
```

If future requirements justify it, components such as a database, task queue, containerization, or distributed workers can be introduced without changing the fundamental concept of a project as a collection of files.

## License

License information will be added later.
