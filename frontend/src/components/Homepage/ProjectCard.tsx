import { useLanguage } from "../../i18n";

interface Project {
  name: string;
  created_at: string;
}

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
}

function ProjectCard({
  project,
  onClick,
}: ProjectCardProps) {
  const { t } = useLanguage();

  const formattedDate = new Date(
    project.created_at
  ).toLocaleString("pl-PL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <button
      className="project-card"
      onClick={onClick}
    >
      <div className="project-card-name">
        {project.name}
      </div>

      <div className="project-card-date">
        {t.projects.created} {formattedDate}
      </div>
    </button>
  );
}

export default ProjectCard;