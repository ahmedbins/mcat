import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import calendar

# Define subjects
subjects = ['Chem', 'Orgo', 'Bio', 'Biochem', 'Math Physics', 'Psych Sociology']


# Function to generate schedule
def generate_schedule(start_date, exam_date, subject_ranks):
    days_until_exam = (exam_date - start_date).days
    schedule = []

    content_phase_days = days_until_exam - 20  # Assume the last 20 days are for practice phase

    # Content Phase
    chapters_per_subject = 12
    subjects_cycle = subject_ranks[::-1] + subject_ranks  # Worst to best subjects cycle
    chapter_days = chapters_per_subject // 3

    current_date = start_date
    for day in range(1, content_phase_days + 1):
        if day > chapter_days * 6:  # Check if all chapters are covered
            break
        morning_subject = subjects_cycle[(day - 1) % 12]
        evening_subject = subjects_cycle[(day - 1 + 6) % 12]

        schedule.append({
            'Date': current_date.strftime('%Y-%m-%d'),
            'Morning': f'{morning_subject} Ch {((day - 1) % chapter_days) * 3 + 1}-{((day - 1) % chapter_days + 1) * 3}',
            'Afternoon/Evening': f'{evening_subject} Ch {((day - 1) % chapter_days) * 3 + 1}-{((day - 1) % chapter_days + 1) * 3}',
            'CARS': '1 passage',
            'Anki': 'Start using Anki' if day > 7 else ''
        })
        current_date += timedelta(days=1)

    # Full-Length Exam and Review
    schedule.append({
        'Date': current_date.strftime('%Y-%m-%d'),
        'Morning': 'Full-Length Exam',
        'Afternoon/Evening': '',
        'CARS': '',
        'Anki': ''
    })
    current_date += timedelta(days=1)
    schedule.append({
        'Date': current_date.strftime('%Y-%m-%d'),
        'Morning': 'Full-Length Review',
        'Afternoon/Evening': '',
        'CARS': '',
        'Anki': ''
    })
    current_date += timedelta(days=1)

    # Practice Phase
    practice_phase_days = days_until_exam - content_phase_days - 2
    for day in range(1, practice_phase_days + 1):
        if (day - 1) % 7 == 5:  # Every 6th day is AAMC full-length exam
            schedule.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Morning': 'AAMC Full-Length Exam',
                'Afternoon/Evening': '',
                'CARS': '',
                'Anki': ''
            })
        elif (day - 1) % 7 == 6:  # Every 7th day is review of the AAMC exam
            schedule.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Morning': 'Review AAMC Full-Length',
                'Afternoon/Evening': '',
                'CARS': '',
                'Anki': ''
            })
        else:
            morning_subject = subjects_cycle[(day - 1) % 12]
            evening_subject = subjects_cycle[(day - 1 + 6) % 12]

            schedule.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Morning': f'Question Banks + Review {morning_subject} chapters',
                'Afternoon/Evening': f'Review {evening_subject} chapters + Anki',
                'CARS': '3-4 passages',
                'Anki': 'Continue using Anki'
            })
        current_date += timedelta(days=1)

    # No studying the day before the exam
    current_date -= timedelta(days=1)
    schedule.append({
        'Date': current_date.strftime('%Y-%m-%d'),
        'Morning': 'Rest day - No studying',
        'Afternoon/Evening': '',
        'CARS': '',
        'Anki': ''
    })

    return schedule


# Function to create calendar view
def create_calendar_view(schedule):
    df_schedule = pd.DataFrame(schedule)
    df_schedule['Date'] = pd.to_datetime(df_schedule['Date'])
    df_schedule.set_index('Date', inplace=True)
    cal = df_schedule[['Morning', 'Afternoon/Evening']].applymap(lambda x: '\n'.join(x.split('+')))
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis('off')
    table = ax.table(cellText=cal.values, rowLabels=cal.index.strftime('%d-%m'), colLabels=cal.columns,
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    return fig


def main():
    st.set_page_config(page_title="MCAT Study Schedule Generator", layout="wide")

    st.title("📚 Custom MCAT Study Schedule Generator")

    st.markdown("""
    Welcome to the MCAT Study Schedule Generator! This tool will help you create a personalized study schedule based on your available time and exam date. Follow the steps below to get started.
    """)

    with st.sidebar:
        st.header("Configuration")
        name = st.text_input("What is your name?", placeholder="Enter your name here")
        start_date = st.date_input("When do you want to start your study schedule?", datetime.today())
        exam_date = st.date_input("When is your MCAT exam date?")

        st.write("Rank your subjects from best (1) to worst (6):")
        subject_ranks = []
        for rank in range(1, 7):
            subject = st.selectbox(f"Rank {rank}", [s for s in subjects if s not in [sr[1] for sr in subject_ranks]],
                                   key=rank)
            subject_ranks.append((rank, subject))

        subject_ranks.sort()
        ranked_subjects = [subject for rank, subject in subject_ranks]

        if st.button("Generate Schedule"):
            if (exam_date - start_date).days <= 0:
                st.error("The exam date must be after the start date.")
            else:
                schedule = generate_schedule(start_date, exam_date, ranked_subjects)
                st.session_state['schedule'] = schedule

    if 'schedule' in st.session_state:
        st.success(f"Custom MCAT study schedule for {name}")

        schedule = st.session_state['schedule']
        df_schedule = pd.DataFrame(schedule)

        st.header("📅 Study Schedule (Table View)")
        st.table(df_schedule)

        st.header("📅 Study Schedule (Calendar View)")
        cal_fig = create_calendar_view(schedule)
        st.pyplot(cal_fig)

        st.header("📊 Progress Graphs")
        df_schedule['Planned Study Hours'] = df_schedule['Morning'].apply(lambda x: 3) + df_schedule[
            'Afternoon/Evening'].apply(lambda x: 3)
        df_schedule['Actual Study Hours'] = df_schedule[
            'Planned Study Hours']  # Placeholder for actual study hours input by the user
        df_schedule['Date'] = pd.to_datetime(df_schedule['Date'])

        fig1 = px.line(df_schedule, x='Date', y='Planned Study Hours', title='Planned Study Hours Over Time')
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(df_schedule, x='Date', y='Actual Study Hours', title='Actual Study Hours Over Time')
        st.plotly_chart(fig2, use_container_width=True)

        st.header("💾 Download Your Schedule")
        csv = df_schedule.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name='mcat_study_schedule.csv',
            mime='text/csv'
        )


if __name__ == "__main__":
    main()
