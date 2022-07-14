from zcs.data.xmlutil import read_questionnaire
import os

XML_INPUT_PATH = os.environ['XML_INPUT_PATH']


def main():
    q = read_questionnaire(XML_INPUT_PATH,
                           with_comments=True)
    print()


if __name__ == '__main__':
    main()
