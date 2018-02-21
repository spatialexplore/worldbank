import pandas
from pandas_datareader import wb
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm
import matplotlib.font_manager

# This script downloads World Bank data on life expectancy for men and women since 1960,
# cleans and processes the data and displays a time-series graph of life expectancy by income
# group. The graph and accompanying explanation are saved in a PDF file (output.pdf).
# Caveat: This script does not include error handling, and functions for downloading and plotting data
# are not generic, but may contain hard-coded values to simplify formatting and output for this particular
# exercise. To be useful for more generic analysis of World Bank Development Indicators, error handling
# should be added, and layout positions calculated relative to size of text, graph and formatting elements.

# Set up font properties and colors for title, legend and axis labels
font_prop = matplotlib.font_manager.FontProperties()
font_prop.set_size(8)
font_color = '#a2a2a2'  # light gray
title_color = '#7f7f7f' # dark gray
matplotlib.rcParams['font.sans-serif'] = 'Verdana'
matplotlib.rcParams['font.family'] = 'sans-serif'

def download_data(ind, country, st_yr, end_yr):
    # Download the indicator(s) for the specified country/countries and start/end years
    # Uses the WorldBank data access extension to Pandas
    dat = wb.download(indicator=ind, country=country, start=st_yr, end=end_yr)
    return dat

# Create a graph within a figure (which is returned), using the data provided.
# X-axis data is specified by x_series, and y_series contains a list of column indices,
# one per data series to be displayed on the graph. Labels for each data series are
# provided in the labels list, and an optional title can be supplied.
def plot_graph(data, x_series, y_series, labels, title=None):
    # Set up a color map for line colors. If more series than colors, repeat the colors.
    # Color codes obtained from Tableau 10 and Tableau 10 Medium color tables
    color_map = ['#e41a1c', '#f4a582', '#377eb8', '#92c5de', '#4daf4a', '#a6d96a', '#984ea3', '#c2a5cf']
    while len(y_series) > len(color_map):
        color_map = color_map.append(color_map)
    colors = color_map[:len(y_series)]

    # Create the figure that will contain the graph and explanatory text
    fig = plt.figure(figsize=(8,11), facecolor='w')

    # Create the graph, and add each data series
    ax = fig.add_subplot(111)
    for s,l,c in zip(y_series, labels, colors):
        # if series is not grouped by two variables (e.g. Income Group and Sex) then don't need to double index.
        if isinstance(s, str):
            ax.plot(x_series, data[s], label=l, color=c)
        else:
            # This example uses this as data is grouped by Income Group and Sex
            ax.plot(x_series, data[s[0]][s[1]], label=l, color=c)

    # Set the graph title if supplied
    if title is not None:
        ax.set_title(title, fontsize=16, ha='center')
        ax.title.set_position((0.5,1.06))
        ax.title.set_color(title_color)

    # Set x-axis labels
    ax.set_xlabel('Year', fontsize=12, ha='center')
    ax.xaxis.label.set_color(font_color)
    ax.xaxis.set_label_coords(0.5, -0.15)

    # Set y-axis labels
    ax.set_ylabel('Age', fontsize=12, ha='center')
    ax.yaxis.label.set_color(font_color)
    ax.yaxis.set_label_coords(-0.05, 0.4)

    # Format axes - no right or top axis lines or ticks, ticks outside the axes, x-axis labels rotated for
    # easier reading.
    ax.tick_params(right='off', top='off', direction='out', colors=font_color, labelsize=12)
    plt.xticks(rotation=60)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_color(font_color)
    ax.spines['bottom'].set_color(font_color)

    # Create a legend below the graph with no frame, two columns and set text color.
    legend = ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center',
                       prop=font_prop, frameon=False, ncol=2)
    plt.setp(legend.get_title(), color=title_color)
    plt.setp(legend.get_texts(), color=title_color)

    # Adjust the location and size of the graph
    plt.subplots_adjust(top=0.6, left=0.1, right=0.9, bottom=0.2)

    # Return the created figure
    return fig


def main():
    # Specify the Life Expectancy indicators (male and female) and download data for all countries between 1960 and now
    indicators = ['SP.DYN.LE00.MA.IN', 'SP.DYN.LE00.FE.IN']
    life_exp = download_data(indicators, ['all'], 1960, 2018)

    # World Bank specifies Income Groups containing countries with economies whose GNI per capita fits within specific
    # thresholds. These groups are already contained within the 'all countries' dataset, so average values do not need
    # to be calculated manually. The four Income Groups are 'Low income economies', 'Lower middle income economies',
    # 'Upper middle income economies' and 'High income economies'.
    # Extract the income groups data from the dataset of all countries
    income_groups = [u'Low income', u'Lower middle income', u'Upper middle income', u'High income']
    life_exp_income = life_exp.select(lambda x: x[0] in income_groups)

    # Rename indicators with more meaningful names, and unstack to index by year rather than country
    col_names = {'SP.DYN.LE00.MA.IN' : 'Male', 'SP.DYN.LE00.FE.IN' : 'Female'}
    life_exp_income = life_exp_income.rename(columns=col_names).unstack(level=0)
    # Swap column grouping to:
    #   Low Income  | Lower Middle Income | Upper Middle Income |  High Income  |
    # Female | Male |   Female  |  Male   |  Female   |  Male   | Female | Male |
    #
    life_exp_income = life_exp_income.swaplevel(0, 1, axis=1)
    life_exp_income = life_exp_income.sortlevel(0, axis=1)

    # While individual countries may have missing data throughout the time-series, in the Income Groups dataset
    # missing data only exists where no data for any of the countries exists - i.e. in the years where no
    # data is available for any of the countries within an income group. Examination of the data shows that
    # this only occurred in 2016 & 2017, and that it occurred across all income groups indicating that the last
    # available data for all income groups was in 2015. The last two rows (2016 & 2017) in life_exp_income
    # contain all NaN values. Since this data is missing across all the columns we wish to display (all income
    # groups), and occurs at the end of the time-series, the simplest way of handling the missing data is to drop
    # those rows and adjust the text to cover the actual range of data.
    #
    # If there had been individual income groups with missing data at points within the time-series, it may have
    # been better to interpolate values to fill in the missing data. If some of the income groups had missing data
    # at the start or end of the time-series, then the year range could have been adjusted to exclude the years
    # where full data was not available.
    life_exp_income_clean = life_exp_income.dropna(how='all')
    last_year = life_exp_income_clean.tail(1).index.item()

    # Findings paragraph
    paragraph = '''Data from the World Bank World Development Indicators dataset shows life
expectancy for both men and women has been steadily improving over the
period 1960-{0}, irrespective of income group, with biggest increases
in Upper Middle income economies. Income group does, however, have a
very strong correlation with life expectancy, with high income economies
showing life expectancies almost 20 years longer than low income
economies for both men and women in {0}. This is an improvement over the
situation in 1960, where the gap between men in high income economies
and those in low income economies was 28 years, and 30 years for women.
Within income groups, the rate of growth in life expectancy for men and
women appear to have been similar since 1960, as evidenced by the
consistent gaps shown between men and women in all groups other than
Lower Middle income economies in the graph below. In this income group,
the gap in life expectancy between men and women is slowly widening,
from 1.3 years in 1960 to 3.7 years in {0}.
'''.format(last_year)

    # Setup data for plotting. The graph will plot a time-series of Life Expectancies for Male and Female for each
    # of the four Income Groups. So there will be 8 y-series provided with corresponding labels.
    series_data = [('Low income','Female'), ('Low income','Male'),
                   ('Lower middle income','Female'), ('Lower middle income','Male'),
                   ('Upper middle income','Female'), ('Upper middle income','Male'),
                   ('High income','Female'), ('High income','Male')]
    series_labels = ['Low income economies (female)', 'Low income economies (male)',
                     'Lower middle income economies (female)', 'Lower middle income economies (male)',
                     'Upper middle income economies (female)', 'Upper middle income economies (male)',
                     'High income economies (female)', 'High income economies (male)']
    # Title for document.
    ttl = 'Trends in Life Expectancy, 1960-{0}'.format(last_year)
    # Generate the graph
    graph_title = 'Life Expectancy by Income Group, 1960-{0}'.format(last_year)
    fig = plot_graph(life_exp_income_clean, life_exp_income_clean.index, series_data, series_labels, graph_title)
    plt.suptitle(ttl, y=0.95, fontsize=20)
    # Add the paragraph text
    fig.text(0.1, 0.65, paragraph, ha='left', va='bottom')
    # Add source information
    fig.text(0.2, 0.03, 'Source: World Development Indicators, The World Bank', color=title_color, size=8)
    # Save the output as a PDF file
    fig.savefig('part_1_output.pdf')
    plt.close()
    return None

if __name__ == '__main__':
    main()


