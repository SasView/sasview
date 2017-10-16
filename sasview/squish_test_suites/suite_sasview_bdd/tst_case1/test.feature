Feature: Opening files in File Explorer

    This test will assure correct behaviour of the file loader

    Scenario: Loading a single 1D file

        Given SasView running
          And empty File Explorer
         When I click on Load Data
         And choose a 1D file
         Then a new index will show up in File Explorer
          And It will be checked

    Scenario: Unselecting the file index
        
        Given SasView running
        And a 1D file loaded
        When I select Uncheck All
        Then the 1D file index will be unchecked

        