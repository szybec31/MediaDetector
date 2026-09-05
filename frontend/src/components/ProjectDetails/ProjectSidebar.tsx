import { useLanguage } from "../../i18n";

interface ProjectSidebarProps {
  onDeleteProject: () => void;
  onDownloadAll: () => void;
  fileCount: number;
}

function ProjectSidebar({
  onDeleteProject,
  onDownloadAll,
  fileCount,
}: ProjectSidebarProps) {
  const { t } = useLanguage();

  return (
    <aside className="project-sidebar">
      <div className="project-sidebar-section">
        <h2>{t.projectDetails.project}</h2>

        <button
          className="project-sidebar-button"
          onClick={onDownloadAll}
          disabled={fileCount === 0}
        >
          <span>↓</span>
          {t.projectDetails.downloadAll}
        </button>

        <button
          className="project-sidebar-button danger"
          onClick={onDeleteProject}
        >
          <span>×</span>
          {t.projectDetails.deleteProject}
        </button>
      </div>
    </aside>
  );
}

export default ProjectSidebar;