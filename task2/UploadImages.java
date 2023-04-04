package com.amazonaws.assignment2a;

import com.amazonaws.AmazonClientException;
import com.amazonaws.AmazonServiceException;
import com.amazonaws.SdkClientException;
import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectRequest;
import com.amazonaws.services.s3.transfer.TransferManager;
import com.amazonaws.services.s3.transfer.TransferManagerBuilder;
import com.amazonaws.services.s3.transfer.Upload;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;

import javax.imageio.ImageIO;

public class UploadImages {

    public static void main(String[] args) throws IOException, AmazonClientException, InterruptedException {
    	Regions clientRegion = Regions.US_EAST_1;
        String bucketName = "s3830776-assignment1";
//        String bucket_prefix = "artists/";
        
        JsonParser parser = new JsonFactory().createParser(new File("a1.json"));
        JsonNode rootNode = new ObjectMapper().readTree(parser);
        JsonNode songsNode = rootNode.get("songs");
        
        
        for (JsonNode songNode : songsNode) {
        	System.out.println("Uploading!");
        	AmazonS3 s3Client = AmazonS3ClientBuilder.standard()
                    .withRegion(clientRegion)
                    .build();
        	
        	String img_Url = songNode.path("img_url").asText();
        	String img_Name = img_Url.substring(img_Url.lastIndexOf('/') + 1);
        	
        	URL url = new URL(img_Url);
        	InputStream in = new BufferedInputStream(url.openStream());
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            int n = 0;
            while (-1 != (n = in.read(buffer))) {
                out.write(buffer, 0, n);
            }
            in.close();
            out.close();
            byte[] data = out.toByteArray();
            
            InputStream inputStream = new ByteArrayInputStream(data);
            
        	try {
                // Upload an image as a new object to s3 bucket
                ObjectMetadata metadata = new ObjectMetadata();
                metadata.setContentLength(data.length);
                PutObjectRequest request = new PutObjectRequest(bucketName, img_Name, inputStream, metadata);
                s3Client.putObject(request);
            } catch (AmazonServiceException e) {
                // The call was transmitted successfully, but Amazon S3 couldn't process 
                // it, so it returned an error response.
                e.printStackTrace();
            } catch (SdkClientException e) {
                // Amazon S3 couldn't be contacted for a response, or the client
                // couldn't parse the response from Amazon S3.
                e.printStackTrace();
            }
        }
        System.out.println("Done!");
        
    }
}

