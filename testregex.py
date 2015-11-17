
import re

p = re.compile(".*?(?P<para>(<p.*?</p>\s*){3,})", re.DOTALL)

t = re.compile("<(?P<tag>.*?)>")

def findparas(text):
    paras = ""
    for i in p.finditer(text):
        paras += t.sub("", i.group("para"))
    return paras
        
def findparas1(text):
    for i in p.finditer(text):
        print t.sub("XXX\g<tag>YYY", i.group("para")) 
        
def findparas2(text):
    for i in p.finditer(text):
        print t.sub(lambda m: m.group("tag")*4, i.group("para"))

text = """

 <!DOCTYPE html>
<html lang="en-GB" id="responsive-news" prefix="og: http://ogp.me/ns#">
<head >
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>The battle in Syria's skies in 60 seconds - BBC News</title>
    <meta name="description" content="The battle in Syria's skies explained in 60 seconds.">

  </div>  </div> <div class="text-wrapper"> <div id="media-asset-page-text">  <h1 class="story-body__h1" data-asset-uri="/news/world-middle-east-34462868">The battle in Syria's skies in 60 seconds</h1>  <p class="date date--v1" data-seconds="1444301751"><strong>8 October 2015</strong> Last updated at 11:55 BST </p>  <div class="map-body display-feature-phone-only"> <p>Russia's dramatic military intervention in the war in Syria has further widened the conflict, now involving the world's major powers.</p><p>Cruise missiles have been fired from warships in the Caspian Sea. And air strikes by Moscow on Syrian rebel and so-called Islamic State (IS) targets have raised the chances of an international incident, with many competing nations now in action in Syrian airspace. </p><p>Add to this picture: Syrian jets targeting rebels since 2012, Israel which has reportedly launched occasional strikes on suspected weapons shipments for Lebanon's Hezbollah movement and a US-led coalition which has carried out more than 2,500 air strikes since 2014.</p><p>With such a large number of countries operating in the area, the risks of a dangerous encounter have increased, as Jonathan Marcus explains. </p><p><i>Video produced by Michael Hirst</i></p>
    </div>  </div> </div> </div> </div> <div class="share-wrapper"> <div class="share share--lightweight  show">
            <a name="share-tools"></a>



"""
