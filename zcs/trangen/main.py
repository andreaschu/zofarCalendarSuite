from zcs.data.xml import read_questionnaire


def main():
    q = read_questionnaire(r'C:\Users\friedrich\zofar_workspace\Test_Modul\src\main\resources\questionnaire.xml', with_comments=True)
    pass


if __name__ == '__main__':
    main()
