// Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

package com.amazonaws.assignment2a;

import java.io.File;

import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class MusicLoadData {

    public static void main(String[] args) throws Exception {

        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard()
        	.withRegion(Regions.US_EAST_1)
            .withCredentials(new ProfileCredentialsProvider("default"))
            .build();

        DynamoDB dynamoDB = new DynamoDB(client);

        Table table = dynamoDB.getTable("music");

        JsonParser parser = new JsonFactory().createParser(new File("a1.json"));

        JsonNode rootNode = new ObjectMapper().readTree(parser);
        JsonNode songsNode = rootNode.get("songs");

        for (JsonNode songNode : songsNode) {
            String title = songNode.get("title").asText();
            String artist = songNode.get("artist").asText();
            int year = songNode.get("year").asInt();
            String web_url = songNode.get("web_url").asText();
            String img_url = songNode.get("img_url").asText();

            try {
                table.putItem(new Item().withPrimaryKey("title", title, "artist", artist)
                		.withNumber("year", year)
                		.withString("web_url", web_url)
                		.withString("img_url", img_url));
                System.out.println("PutItem succeeded: " + title + " " + artist + " " + year + " " + web_url + " " + img_url);
            }
            catch (Exception e) {
                System.err.println("Unable to add music: " + title + " " + artist);
                System.err.println(e.getMessage());
                break;
            }
        }
        parser.close();
    }
}