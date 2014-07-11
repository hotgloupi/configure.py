Feature: Initialize project file

    Scenario: Launch configure script
        Given a temporary directory
        When I configure with --init
        Then A .config directory is created
        And a project config file is created

    Scenario: Cannot initialize twice
        Given an initialized directory
        When I configure with --init
        Then configure failed
