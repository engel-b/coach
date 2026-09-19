import coachAvatarUrl from "../assets/coach-avatar.webp";

interface CoachAvatarProps {
  className?: string;
  label?: string;
}

export function CoachAvatar({
  className = "",
  label = "Coach",
}: CoachAvatarProps) {
  const classes = ["coach-portrait", className].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      <img src={coachAvatarUrl} alt="" aria-hidden="true" />
      {label !== "" && <span>{label}</span>}
    </div>
  );
}
