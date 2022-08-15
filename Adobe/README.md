# Adobe CC Admin Console App Packaging

Usage

The [Adobe CC Admin Console Packages.pkg.recipe](https://github.com/woodmember/Woodmember-Autopkg-Recipes/blob/main/Adobe/Adobe%20CC%20Admin%20Console%20Packages.pkg.recipe "Adobe CC Admin Console Packages.pkg.recipe") recipe is designed for you to create a .pkg from any Adobe Admin Console Package. This is intended for use for those managing SDL licenses & / or installs.

1. Naming is important to the recipes, to start with you'll need to create [Managed Package](https://helpx.adobe.com/uk/enterprise/using/manage-packages.html) with one of the below names in the [Adobe Admin Console](https://adminconsole.adobe.com/):

|     |     |     |     |
| --- | --- | --- | --- |
| AdobeAcrobatDC | AdobeCharacterAnimator2021 | AdobeInDesign2022 | AdobePremiereRush |
| AdobeAfterEffects2021 | AdobeCharacterAnimator2022 | AdobeLightroomCC | AdobePremiereRush2.0 |
| AdobeAfterEffects2022 | AdobeDimension | AdobeLightroomClassic | AdobeSubstance3DDesigner |
| AdobeAnimate2021 | AdobeDreamweaver2021 | AdobeMediaEncoder2021 | AdobeSubstance3DPainter |
| AdobeAnimate2022 | AdobeIllustrator2021 | AdobeMediaEncoder2022 | AdobeSubstance3DSampler |
| AdobeAudition2021 | AdobeIllustrator2022 | AdobePhotoshop2021 | AdobeSubstance3DStager |
| AdobeAudition2022 | AdobeInCopy2021 | AdobePhotoshop2022 | AdobeXD |
| AdobeBridge2021 | AdobeInCopy2022 | AdobePremierePro2021 |     |
| AdobeBridge2022 | AdobeInDesign2021 | AdobePremierePro2022 |     |

Note:

The [Adobe CC Admin Console Packages.pkg.recipe](https://github.com/woodmember/Woodmember-Autopkg-Recipes/blob/main/Adobe/Adobe%20CC%20Admin%20Console%20Packages.pkg.recipe "Adobe CC Admin Console Packages.pkg.recipe") recipe requires the above naming convention to be followed. When creating a override the "NAME" input needs one of the above names in order for the packaging process to work

2. Download the Desired Adobe CC DMG from the [Adobe Admin Console](https://adminconsole.adobe.com/)
3. Load the .app
4. Download the Adobe CC Installer .Zip to your desired working directory

Note:

The [Adobe CC Admin Console Packages.pkg.recipe](https://github.com/woodmember/Woodmember-Autopkg-Recipes/blob/main/Adobe/Adobe%20CC%20Admin%20Console%20Packages.pkg.recipe "Adobe CC Admin Console Packages.pkg.recipe") recipe requires the path to this working directory. When creating a override, enter this path into the "CCPKGPATH" input.

5. Create a override of the [Adobe CC Admin Console Packages.pkg.recipe](https://github.com/woodmember/Woodmember-Autopkg-Recipes/blob/main/Adobe/Adobe%20CC%20Admin%20Console%20Packages.pkg.recipe "Adobe CC Admin Console Packages.pkg.recipe") recipe, entering in the "NAME" & "CCPKGPATH" varibles as mentioned above
