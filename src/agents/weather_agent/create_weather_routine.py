from azure.ai.projects.models import (
    InvokeAgentResponsesApiRoutineAction,
    ScheduleRoutineTrigger,
)

from agents.routines import create

def main() -> None:
    create(
        routine_name="weekday-weather-brussels",
        description="Provides a weekday morning weather report.",
        enabled=False,
        triggers={
            "daily-morning": ScheduleRoutineTrigger(
                cron_expression="30 9 * * *",
                time_zone="Europe/Brussels",
            ),
        },
        action=InvokeAgentResponsesApiRoutineAction(
            agent_name="weather-agent",
            input="Report today's weather for Brussels, Belgium.",
        ),
    )

if __name__ == "__main__":
    main()