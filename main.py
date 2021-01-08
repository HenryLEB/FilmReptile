from functions import *


def main():
    firm_name = input('请输入要爬取影评的电影名称： ')
    # firm_name = '八佰'

    firm_details_url = getFirmDetailsUrl(firm_name)
    filmReviewUrl = getFilmReviewUrl(firm_details_url)
    saveDataToCSV(getAllReviews(filmReviewUrl))

    csvFile = pd.read_csv('评论.csv', encoding='utf-8')
    str_reviews = getStrReview(csvFile)
    #
    drawReviewsCloud(str_reviews)
    drawSatisfactionAnalysisDiagram(csvFile)
    drawPeriodOfTimeHistogram(csvFile)


if __name__ == '__main__':
    main()
