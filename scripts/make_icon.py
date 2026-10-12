from pathlib import Path
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parents[1]
folder=root/'assets';folder.mkdir(exist_ok=True)
image=Image.new('RGB',(432,432),'#101722');d=ImageDraw.Draw(image)
scale=4
def points(p):return [(x*scale,y*scale) for x,y in p]
d.polygon(points([(54,21),(83,38),(83,70),(54,87),(25,70),(25,38)]),fill='#36c8b2')
d.polygon(points([(54,54),(83,38),(83,70),(54,87)]),fill='#227c7b')
d.polygon(points([(54,21),(83,38),(54,54),(25,38)]),fill='#51e1c6')
d.polygon(points([(54,29),(75,41),(54,53),(33,41)]),fill='#101722')
d.rectangle((49*scale,37*scale,59*scale,47*scale),fill='#ecf4fa')
for p in [[(17,35),(17,23),(29,23)],[(79,23),(91,23),(91,35)],[(17,73),(17,85),(29,85)],[(79,85),(91,85),(91,73)]]:
    d.line(points(p),fill='#ecf4fa',width=12)
image.save(folder/'icon.png')
image.save(folder/'icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
