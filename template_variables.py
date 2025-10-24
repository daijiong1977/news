#!/usr/bin/env python3
"""
Email Template Variables

These variables are used in email_template_conditional.html
with Jinja2 conditional logic to show level-specific content.

Usage in Buttondown:
1. Copy email_template_conditional.html to Buttondown
2. Use these variables in the template:
   - {{ article_body_easy }}
   - {{ article_body_mid }}
   - {{ article_body_hard }}
   - {{ article_body_CN }}
"""

# Article content for each difficulty level
# These are HTML strings that replace {{ article_body_* }} in the template


article_body_easy = """<div class="article">
                    <img src="http://localhost:8000/api/images/article_9_8fdf885cffc0.jpg" alt="Big New Party Room at the White House" class="article-image" loading="lazy">
                    <div class="article-content">
                        <div class="article-id">Article #9</div>
                        <div class="article-title">Big New Party Room at the White House</div>
                        <div class="article-summary">The White House is getting a huge new ballroom where people can have parties and events. This new room will be very big - almost twice as large as the main White House building itself. It will be able to hold 999 people at once. The President says this new ballroom won't cost taxpayers any money because private donors are paying for it. Construction has already started, and workers are taking down part of the East Wing to build this new space. The President says the White House needs a bigger party space because the current largest room only holds about 200 people. Some money for the project came from YouTube as part of a legal settlement. The White House promised to share who donated money but hasn't given a full list yet. They also haven't said how much money the President himself is giving. Originally, they said the White House building wouldn't be touched, but now they are taking down part of the East Wing facade.</div>
                    </div>
                </div>"""

article_body_mid = """<div class="article">
                    <img src="http://localhost:8000/api/images/article_9_8fdf885cffc0.jpg" alt="Trump's $250 Million White House Ballroom Expansion" class="article-image" loading="lazy">
                    <div class="article-content">
                        <div class="article-id">Article #9</div>
                        <div class="article-title">Trump's $250 Million White House Ballroom Expansion</div>
                        <div class="article-summary">Construction has commenced on a $250 million ballroom addition to the White House, with demolition of the East Wing facade underway. The 90,000-square-foot structure will significantly exceed the size of the main White House building, nearly doubling its footprint. President Trump asserts the project will accommodate 999 guests, addressing what he describes as inadequate entertainment space in the current White House facilities. The East Room, currently the largest entertainment space, holds approximately 200 people, leading to previous administrations hosting large events in temporary tents on the South Lawn. Funding for the project comes entirely from private sources according to the administration, including $22 million from YouTube as part of a legal settlement from a 2021 lawsuit. While the White House has committed to disclosing donor information, no comprehensive list has been released. The administration initially claimed the White House structure would remain untouched, but demolition work contradicts these earlier assurances. The East Wing traditionally serves as the social entrance for White House events and sits adjacent to the Treasury Department.</div>
                    </div>
                </div>"""

article_body_hard = """<div class="article">
                    <img src="http://localhost:8000/api/images/article_9_8fdf885cffc0.jpg" alt="Architectural Expansion and Funding Mechanisms of Trump's White House Ballroom Project" class="article-image" loading="lazy">
                    <div class="article-content">
                        <div class="article-id">Article #9</div>
                        <div class="article-title">Architectural Expansion and Funding Mechanisms of Trump's White House Ballroom Project</div>
                        <div class="article-summary">The Trump administration has initiated construction of a $250 million ballroom addition to the White House complex, commencing with demolition of the East Wing facade. This 90,000-square-foot structure will substantially exceed the spatial footprint of the main Executive Residence, representing nearly double its square footage with capacity for 999 occupants. The project rationale centers on addressing perceived inadequacies in current entertainment facilities, particularly the East Room's 200-person capacity limitation that has necessitated temporary tent structures on the South Lawn for large-scale events. Funding mechanisms involve exclusively private sources, including a $22 million contribution from YouTube originating from settlement proceedings of litigation initiated by President Trump in 2021. The administration maintains that taxpayer funds will not be utilized, though comprehensive donor disclosure remains pending despite earlier transparency commitments. Methodological concerns arise from contradictory assurances regarding structural preservation—initial statements claimed the White House would remain physically untouched, yet facade demolition indicates significant architectural alteration. The East Wing's historical role as the social entrance and its proximity to the Treasury Department introduce additional considerations regarding security protocols, ceremonial functions, and historical preservation standards. The project represents a substantial intervention in federal architecture with implications for donor influence, preservation ethics, and executive discretion over nationally significant properties.</div>
                    </div>
                </div>"""

article_body_CN = """<div class="article">
                    <img src="http://localhost:8000/api/images/article_9_8fdf885cffc0.jpg" alt="关于特朗普为白宫增建2.5亿美元舞厅需要了解的9件事" class="article-image" loading="lazy">
                    <div class="article-content">
                        <div class="article-id">Article #9</div>
                        <div class="article-title">关于特朗普为白宫增建2.5亿美元舞厅需要了解的9件事</div>
                        <div class="article-summary">美联社达琳·苏珀维尔报道 华盛顿（美联社）——本周，特朗普总统为白宫增建的2.5亿美元舞厅已开始施工，建筑工人开始拆除东翼的外立面，新舞厅将在此建造。这个9万平方英尺的舞厅将使白宫主建筑相形见绌，面积近乎翻倍，特朗普表示可容纳999人。特朗普在社交媒体上声称，舞厅不会花费纳税人一分钱，因为资金全部来自“许多慷慨的爱国者、伟大的美国公司以及本人”的私人捐款。以下是关于这一最新白宫建设项目需要了解的信息。特朗普表示白宫需要大型娱乐空间，并抱怨目前白宫内最大的东厅只能容纳约200人，空间太小。他对以往总统在南草坪帐篷内举办国宴等大型活动的做法表示不满。特朗普声称项目资金将全部来自私人捐款，不会动用公共资金。白宫承诺将公布承诺捐款或已捐款的个人和公司信息，上周还邀请部分捐款人参加了东厅晚宴，但尚未发布完整的捐款人名单和资金明细。其中2200万美元来自谷歌子公司YouTube，这是特朗普2021年起诉该公司达成和解协议的一部分。白宫也未透露特朗普本人出资多少。东翼传统上是白宫的社交区域，位于财政部对面的东行政大道旁，是游客和其他宾客参加活动的入口。总统及其首席发言人卡洛琳·莱维特今年夏季曾表示，建造舞厅期间白宫主体建筑将保持完好。特朗普说：“它会靠近但不会接触主体建筑。”莱维特补充道：“不会拆除任何建筑。”但实际情况并非如此。</div>
                    </div>
                </div>"""
