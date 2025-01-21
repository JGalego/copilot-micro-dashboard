# pylint: disable=redefined-outer-name
r"""
GitHub Copilot Metrics Explorer
https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage
            ______
         .-'      `-.
       .'            `.
      /                \
     ;                 ;`
     |       GHC       |;
     ;                 ;|
     '\               / ;
      \`.           .' /
       `.`-._____.-' .'
         / /`_____.-'
        / / /
       / / /
      / / /
     / / /
    / / /
   / / /
  / / /
 / / /
/ / /
\/_/
"""

import functools
import operator
import os

from collections import Counter
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

DEFAULT_API_VERSION = "2022-11-28"

ACCOUNT_TYPE_MAP = {
    'Enterprise': "enterprises",
    'Organization': "orgs",
}

def get_copilot_usage_metrics(
        account_name: str,
        account_type: str,
        token: str, api_version:
        str = DEFAULT_API_VERSION) -> Dict:
    """Get the Copilot usage metrics for your organization or enterprise account"""
    response = requests.get(
        f"https://api.github.com/{account_type}/{account_name}/copilot/metrics",
        headers={
            'Accept': "application/vnd.github+json",
            'Authorization': f"Bearer {token}",
            'X-GitHub-Api-Version': api_version,
        },
        timeout=5,
    )
    return response.json()

def get_metrics_by_date(metrics: Dict) -> Dict:
    """Returns a dictionary of metrics by date"""
    metrics_by_date = {}
    for metric in metrics:
        metrics_by_date[metric.pop('date')] = metric
    return metrics_by_date

def get_daily_active_users(metrics: Dict) -> pd.DataFrame:
    """Returns a timeseries of daily *active* users"""
    daily_active_users = {'date': metrics.keys()}
    daily_active_users['active'] = [
        metric['total_active_users'] for metric in metrics.values()
    ]
    df = pd.DataFrame(daily_active_users)
    df.set_index('date', inplace=True)
    return df

def get_daily_engaged_users(metrics: Dict) -> pd.DataFrame:
    """Returns a timeseries daily *engaged* users"""
    daily_engaged_users = {'date': metrics.keys()}
    daily_engaged_users['engaged'] = [
        metric['total_engaged_users'] for metric in metrics.values()
    ]
    df = pd.DataFrame(daily_engaged_users)
    df.set_index('date', inplace=True)
    return df

def get_ide_code_completions_by_editor(metrics: Dict, date: str) -> Dict:
    """Returns IDE code completions by editor for a given date"""
    editors = {
        editor['name']: editor['total_engaged_users'] \
            for editor in metrics[date]['copilot_ide_code_completions']['editors']
    }
    return editors

def get_total_ide_completions_by_editor(metrics: Dict):
    """Returns the total IDE code completions by editor"""
    ide_completions = [
        get_ide_code_completions_by_editor(metrics, date) for date in metrics.keys()
    ]
    total_ide_completions = dict(functools.reduce(operator.add, map(Counter, ide_completions)))
    return total_ide_completions

def get_ide_code_completions_by_language(metrics: Dict, date: str) -> Dict:
    """Returns IDE code completions by language for a given date"""
    languages = {
        language['name']: language['total_engaged_users'] \
            for language in metrics[date]['copilot_ide_code_completions']['languages']
    }
    return languages

def get_total_ide_completions_by_language(metrics: Dict):
    """Returns the total IDE code completions by language"""
    ide_completions = [
        get_ide_code_completions_by_language(metrics, date) for date in metrics.keys()
    ]
    total_ide_completions = dict(functools.reduce(operator.add, map(Counter, ide_completions)))
    return total_ide_completions

def get_acception_rates_by_language(metrics: Dict):
    """Returns the rejection rates by language"""
    acceptance_rates = {}
    for metric in metrics.values():
        for editor in metric['copilot_ide_code_completions']['editors']:
            for model in editor['models']:
                for language in model['languages']:
                    if language['name'] in acceptance_rates:
                        acceptance_rates[language['name']]['acceptances'] \
                            += language['total_code_acceptances']
                        acceptance_rates[language['name']]['suggestions'] \
                            += language['total_code_suggestions']
                        acceptance_rates[language['name']]['lines_accepted'] \
                            += language['total_code_lines_accepted']
                        acceptance_rates[language['name']]['lines_suggested'] \
                            += language['total_code_lines_suggested']
                    else:
                        acceptance_rates[language['name']] = {
                            'acceptances': language['total_code_acceptances'],
                            'suggestions': language['total_code_suggestions'],
                            'lines_accepted': language['total_code_lines_accepted'],
                            'lines_suggested': language['total_code_lines_suggested'],
                        }

    for language in acceptance_rates.values():
        language['acceptance_rate'] = language['acceptances'] / \
                                      language['suggestions']
        language['lines_acceptance_rate'] = language['lines_accepted'] / \
                                            language['lines_suggested']

    return acceptance_rates

st.set_page_config(
    page_title="Copilot Metrics Explorer 🧐",
    page_icon="🧐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get account details
account_name = st.sidebar.text_input('Account Name', os.getenv('GITHUB_ACCOUNT'))
account_type = st.sidebar.selectbox('Account Type', ["Enterprise", "Organization"], index=0)

# Retrieve GH token
token = st.sidebar.text_input('GitHub Token', os.getenv('GITHUB_TOKEN'), type='password')

# Get Copilot usage metrics
if st.sidebar.button('Get Usage Metrics 📈'):
    metrics = get_copilot_usage_metrics(account_name, ACCOUNT_TYPE_MAP[account_type], token)
    metrics = get_metrics_by_date(metrics)

    st.markdown("### Total Users 👨‍💻")

    daily_active_users = get_daily_active_users(metrics)
    daily_engaged_users = get_daily_engaged_users(metrics)
    total_users = daily_active_users.join(daily_engaged_users)
    st.line_chart(total_users, color=["#f00", "#00f"])

    st.markdown("### Copilot IDE Code Completions by Editor 💻")

    total_ide_completions_by_editor = get_total_ide_completions_by_editor(metrics)
    total_ide_completions_by_editor = dict(
        sorted(total_ide_completions_by_editor.items(),
               key=lambda editor: editor[1], reverse=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    wedges, _, _ = ax.pie(
        total_ide_completions_by_editor.values(),
        autopct='%.1f%%',
        startangle=140
    )
    ax.legend(
        wedges,
        total_ide_completions_by_editor.keys(),
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1)
    )
    ax.axis('equal')
    st.pyplot(fig)

    st.markdown("### Copilot IDE Code Completions by Language ♨️")

    total_ide_completions_by_language = get_total_ide_completions_by_language(metrics)
    total_ide_completions_by_language = dict(
        sorted(total_ide_completions_by_language.items(),
               key=lambda language: language[1])
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(
        total_ide_completions_by_language.keys(),
        total_ide_completions_by_language.values(),
        height=0.4
    )
    ax.tick_params(axis='y', labelsize=8)
    st.pyplot(fig)

    st.markdown("### Copilot Acceptance Rates by Language 📊")

    acceptance_rates = get_acception_rates_by_language(metrics)
    acceptance_rates_df = pd.DataFrame(acceptance_rates).T\
                            .sort_values('suggestions', ascending=False)
    acceptance_rates_df = acceptance_rates_df.astype({
        'acceptances': int,
        'suggestions': int,
        'lines_accepted': int,
        'lines_suggested': int,
    })
    acceptance_rates_df['acceptance_rate'] = \
        acceptance_rates_df['acceptance_rate'].apply(lambda x: f"{x:.1%}")
    acceptance_rates_df['lines_acceptance_rate'] = \
        acceptance_rates_df['lines_acceptance_rate'].apply(lambda x: f"{x:.1%}")
    st.table(acceptance_rates_df)
else:
    st.markdown("""
# Copilot Metrics Explorer 🧐
A simple dashboard for visualizing usage metrics from [GitHub Copilot](https://github.com/features/copilot) using the [Metrics](https://docs.github.com/en/rest/copilot/copilot-metrics) and [User Management APIs](https://docs.github.com/en/rest/copilot/copilot-user-management).
To get started, please provide your GitHub account name, account type (organization or enterprise), and a personal access token with the necessary permissions to access the Copilot metrics.
You can create a personal access token by following these [instructions](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token).
![](https://techcrunch.com/wp-content/uploads/2023/03/copilot_chat-3.gif)
""")
