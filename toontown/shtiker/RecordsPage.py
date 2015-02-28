import ShtikerPage
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
import webbrowser
from direct.gui.OnscreenText import OnscreenText


class RecordsPage(ShtikerPage.ShtikerPage):
    def soloVP(self):
        webbrowser.open_new('https://www.youtube.com/watch?v=BuRsmYr6cLU')

    def duoVP(self):
        webbrowser.open_new('https://www.youtube.com/watch?v=PSDr2XCHu_0')

    def myTab(self):
        VPRecord10 = OnscreenText(text = 'Fastest VP Solo\n Howling Ninja Dog\n Total Time 14:31\n Pie Round Time = 4:55', pos = (-0.47, 0.5), scale = 0.07, font = loader.loadFont('phase_3/models/fonts/ImpressBT.ttf'))
        VPRecord10.reparentTo(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.RecordsPageTitle, text_scale=0.1, pos=(0, 0, 0.65))

        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        self.VPTab = DirectButton(parent=self, relief=None, text=TTLocalizer.RecordsPageTitleVP, text_scale=TTLocalizer.FPtankTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.myTab, pos=(0.92, 0, 0.55))
        self.CFOTab = DirectButton(parent=self, relief=None, text=TTLocalizer.RecordsPageTitleCFO, text_scale=TTLocalizer.FPtankTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.myTab, pos=(0.92, 0, 0.55))
        self.CJTab = DirectButton(parent=self, relief=None, text=TTLocalizer.RecordsPageTitleCJ, text_scale=TTLocalizer.FPtankTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface3'), image_pos=(-0.28, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.myTab, pos=(0.92, 0, -0.3))
        self.CEOTab = DirectButton(parent=self, relief=None, text=TTLocalizer.RecordsPageTitleCEO, text_scale=TTLocalizer.FPtankTab, text_align=TextNode.ALeft, image=gui.find('**/tabs/polySurface3'), image_pos=(-0.28, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.myTab, pos=(0.92, 0, -0.3))
        self.VPTab.setPos(-0.85, 0, 0.775)
        self.CFOTab.setPos(-0.43, 0, 0.775)
        self.CJTab.setPos(0.11, 0, 0.775)
        self.CEOTab.setPos(0.53, 0, 0.775)

        VPRecord1 = OnscreenText(text = 'Fastest VP Solo\n Howling Ninja Dog\n Total Time 14:31\n Pie Round Time = 4:55', pos = (-0.47, 0.5), scale = 0.07, font = loader.loadFont('phase_3/models/fonts/ImpressBT.ttf'))
        VPRecord1.reparentTo(self)

        VPRecord2 = OnscreenText(text = 'Fastest VP Duo\n Master Jake Electrowoof &\n Sav\n Total Time 10:39\n Pie Round Time = 5:01', pos = (-0.47, 0), scale = 0.07, font = loader.loadFont('phase_3/models/fonts/ImpressBT.ttf'))
        VPRecord2.reparentTo(self)

        ButtonImage = loader.loadModel("phase_3/models/gui/quit_button.bam")
        ImgBtn3 = DirectButton(frameSize=None, text='Solo VP', image=(ButtonImage.find('**/QuitBtn_UP'), \
        ButtonImage.find('**/QuitBtn_DN'), ButtonImage.find('**/QuitBtn_RLVR')), relief=None, command=self.soloVP, text_pos=(0, -0.015), \
        geom=None, pad=(0.01, 0.01), suppressKeys=0, pos = (0.5, 0.8, 0.12), text_scale=0.059, borderWidth=(0.015, 0.01), scale=.7)

        ImgBtn3.reparentTo(self)

        ButtonImage = loader.loadModel("phase_3/models/gui/quit_button.bam")
        ImgBtn4 = DirectButton(frameSize=None, text='Duo VP', image=(ButtonImage.find('**/QuitBtn_UP'), \
        ButtonImage.find('**/QuitBtn_DN'), ButtonImage.find('**/QuitBtn_RLVR')), relief=None, command=self.duoVP, text_pos=(0, -0.015), \
        geom=None, pad=(0.01, 0.01), suppressKeys=0, pos = (0.2, 0.8, 0.12), text_scale=0.059, borderWidth=(0.015, 0.01), scale=.7)

        ImgBtn4.reparentTo(self)
