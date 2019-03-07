from PIL import Image
from solve_captcha import demo

demo(Image.open('captcha-demo/captcha.jpg')).save('captcha-demo/solution.jpg')
