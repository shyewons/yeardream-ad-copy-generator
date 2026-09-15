# 입력과 출력의 형식과 검증 규칙을 정의하는 파일
# 필수 항목이나 자료형이 맞지 않은 응답을 확인 한다.
# 글자 수나 해시태그 개수 제한도 여기서 추가할 수 있다.
from pydantic import BaseModel, Field


# 광고 생성 요청시 어떤 데이터가 필요한지 정의하는 클래스
# BaseModel: Pydantic의 데이터 검증 기능을 상속
class AdRequest(BaseModel):
    product_name: str = Field(min_length=1, max_length=100)
    features : str = Field(min_length=1, max_length=1000)
    target : str = Field(min_length=1, max_length=200)
    channel : str = Field(min_length=1, max_length=50)
    tone : str = Field(min_length=1, max_length=50)

# max_length는 자료형에 따라 의미가 달라짐
# str이면 글자수, list면 항목수
class AdCopy(BaseModel):
    headline: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=1000)
    cta: str = Field(min_length=1, max_length=100)
    hashtags: list[str] = Field(max_length=5)