def create_incident_reply(imgur_link, days_since_last_incident, count_in_2023, total_incidents):
    full_comment = (
                        f'![It has been {days_since_last_incident} days since the last time a truck hit an overpass in British Columbia!]({imgur_link})\n'
                        f'\n\n'
                        f'**Stats:**  \n'
                        f'**Number of incidents in 2023:** {count_in_2023}  \n'
                        f'**Number of databased incidents:** {total_incidents}\n'
                    )
    return full_comment

def create_stats_comment(last_date, total, longest, shortest):
    stats_comment = (
                            f"**Last incident was on:** {last_date}  \n"
                            f"**Total number of incidents:** {total}  \n"
                            f"**Longest streak between incidents:** {longest} days  \n"
                            f"**Shortest streak between incidents:** {shortest} days  \n"
                            f"  \n"
                            f"Fun fact! The shortest streak is zero because on June 8th, 2023 there were two incidents in the same day."
                        )
    return stats_comment