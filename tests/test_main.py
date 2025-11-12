"""
메인 모듈 테스트
"""

import pytest
from myproject.main import main


def test_main(capsys):
    """main 함수 테스트"""
    main()
    captured = capsys.readouterr()
    assert "Hello, Python Project!" in captured.out


if __name__ == "__main__":
    pytest.main([__file__])

