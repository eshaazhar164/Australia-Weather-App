import pandas as pd
import seaborn as sns
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import io
import base64


def create_chart(
    weather_data,
    x_column,
    y_column,
    title,
    y_label,
    bar_color
):
    if not weather_data:
        return None

    df = pd.DataFrame(weather_data)

    if x_column not in df.columns or y_column not in df.columns:
        return None

    df[y_column] = pd.to_numeric(
        df[y_column],
        errors="coerce"
    )

    df = df.dropna(subset=[x_column, y_column])

    if df.empty:
        return None

    sns.set_theme(style="whitegrid", context="notebook")

    fig, ax = plt.subplots(figsize=(11, 6))

    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8faff")

    sns.barplot(
        data=df,
        x=x_column,
        y=y_column,
        color=bar_color,
        edgecolor="white",
        linewidth=1.5,
        ax=ax
    )

    # Display values above bars
    for container in ax.containers:
        ax.bar_label(
            container,
            fmt="%.1f",
            padding=5,
            fontsize=10,
            fontweight="bold",
            color="#263554"
        )

    # Start y-axis at zero
    maximum = df[y_column].max()

    if pd.notna(maximum):
        ax.set_ylim(
            bottom=0,
            top=max(maximum * 1.20, 1)
        )

    # Chart title
    ax.set_title(
        title,
        fontsize=16,
        fontweight="bold",
        color="#172b4d",
        pad=22
    )

    # Axis labels
    ax.set_xlabel(
        "Australian Cities",
        fontsize=12,
        fontweight="bold",
        color="#263554",
        labelpad=12
    )

    ax.set_ylabel(
        y_label,
        fontsize=12,
        fontweight="bold",
        color="#263554",
        labelpad=12
    )

    # City names and axis styling
    ax.tick_params(
        axis="x",
        labelsize=10,
        labelcolor="#263554",
        rotation=25
    )

    ax.tick_params(
        axis="y",
        labelsize=10,
        labelcolor="#52627a"
    )

    # Gridlines
    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.7,
        alpha=0.35
    )

    ax.grid(axis="x", visible=False)

    # Remove extra borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dce3ef")
    ax.spines["bottom"].set_color("#dce3ef")

    plt.tight_layout(pad=2)

    # Convert chart to Base64 image
    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=160,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    buffer.seek(0)

    chart = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    plt.close(fig)
    buffer.close()

    return chart


def create_temperature_chart(weather_data):
    return create_chart(
        weather_data,
        "city",
        "current_temperature",
        "Current Temperature in Australian Cities",
        "Temperature (°C)",
        "#4169e1"
    )


def create_humidity_chart(weather_data):
    return create_chart(
        weather_data,
        "city",
        "humidity",
        "Humidity Comparison Across Australian Cities",
        "Humidity (%)",
        "#16a6a1"
    )


def create_uv_chart(weather_data):
    return create_chart(
        weather_data,
        "city",
        "uv_index",
        "Current UV Index in Australian Cities",
        "UV Index",
        "#f59e0b"
    )