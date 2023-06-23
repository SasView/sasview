from django.db import models

# do we want individual dbs for each model 
class fits(models.Model):

    name = models.CharField(max_length=200, help_text="The name for all the fit data")
    server = models.CharField(max_length=200)
    #fin later : category = models.ForeignKey()
    username = models.CharField(max_length=100, blank=False, null=False)
    password = models.CharField(max_length=100, blank=False, null=False)
    enabled = models.BooleanField(blank=False, null=False, default=True)
    
    #model category
    #model name
    #structure factor
    #options: polydespersity, 2d view, magnitism (future)
    #fit range
    #data points
    #weighting
    #instrument smearing
    #magnitism angles