/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.commons.fileupload;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;

import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.junit.Test;

/**
 * Serialization Unit tests for
 *  {@link org.apache.commons.fileupload.disk.DiskFileItem}.
 *
 * @version $Id$
 */
public class DiskFileItemSerializeTest {

    /**
     * Content type for regular form items.
     */
    private static final String textContentType = "text/plain";

    /**
     * Very low threshold for testing memory versus disk options.
     */
    private static final int threshold = 16;

    /**
     * Test creation of a field for which the amount of data falls below the
     * configured threshold.
     */
    @Test
    public void testBelowThreshold() throws Exception {
        // Create the FileItem
        byte[] testFieldValueBytes = createContentBytes(threshold - 1);
        FileItem item = createFileItem(testFieldValueBytes);

        // Check state is as expected
        assertTrue("Initial: in memory", item.isInMemory());
        assertEquals("Initial: size", item.getSize(), testFieldValueBytes.length);
        compareBytes("Initial", item.get(), testFieldValueBytes);

        // Serialize & Deserialize
        FileItem newItem = (FileItem)serializeDeserialize(item);

        // Test deserialized content is as expected
        assertTrue("Check in memory", newItem.isInMemory());
        compareBytes("Check", testFieldValueBytes, newItem.get());

        // Compare FileItem's (except byte[])
        compareFileItems(item, newItem);
    }

    /**
     * Test creation of a field for which the amount of data equals the
     * configured threshold.
     */
    @Test
    public void testThreshold() throws Exception {
        // Create the FileItem
        byte[] testFieldValueBytes = createContentBytes(threshold);
        FileItem item = createFileItem(testFieldValueBytes);

        // Check state is as expected
        assertTrue("Initial: in memory", item.isInMemory());
        assertEquals("Initial: size", item.getSize(), testFieldValueBytes.length);
        compareBytes("Initial", item.get(), testFieldValueBytes);


        // Serialize & Deserialize
        FileItem newItem = (FileItem)serializeDeserialize(item);

        // Test deserialized content is as expected
        assertTrue("Check in memory", newItem.isInMemory());
        compareBytes("Check", testFieldValueBytes, newItem.get());

        // Compare FileItem's (except byte[])
        compareFileItems(item, newItem);
    }

    /**
     * Test creation of a field for which the amount of data falls above the
     * configured threshold.
     */
    @Test
    public void testAboveThreshold() throws Exception {
        // Create the FileItem
        byte[] testFieldValueBytes = createContentBytes(threshold + 1);
        FileItem item = createFileItem(testFieldValueBytes);

        // Check state is as expected
        assertFalse("Initial: in memory", item.isInMemory());
        assertEquals("Initial: size", item.getSize(), testFieldValueBytes.length);
        compareBytes("Initial", item.get(), testFieldValueBytes);

        // Serialize & Deserialize
        FileItem newItem = (FileItem)serializeDeserialize(item);

        // Test deserialized content is as expected
        assertFalse("Check in memory", newItem.isInMemory());
        compareBytes("Check", testFieldValueBytes, newItem.get());

        // Compare FileItem's (except byte[])
        compareFileItems(item, newItem);
    }

    /**
     * Compare FileItem's (except the byte[] content)
     */
    private void compareFileItems(FileItem origItem, FileItem newItem) {
        assertTrue("Compare: is in Memory",   origItem.isInMemory()   == newItem.isInMemory());
        assertTrue("Compare: is Form Field",  origItem.isFormField()  == newItem.isFormField());
        assertEquals("Compare: Field Name",   origItem.getFieldName(),   newItem.getFieldName());
        assertEquals("Compare: Content Type", origItem.getContentType(), newItem.getContentType());
        assertEquals("Compare: File Name",    origItem.getName(),        newItem.getName());
    }

    /**
     * Compare content bytes.
     */
    private void compareBytes(String text, byte[] origBytes, byte[] newBytes) {
        assertNotNull("origBytes must not be null", origBytes);
        assertNotNull("newBytes must not be null", newBytes);
        assertEquals(text + " byte[] length", origBytes.length, newBytes.length);
        for (int i = 0; i < origBytes.length; i++) {
            assertEquals(text + " byte[" + i + "]", origBytes[i], newBytes[i]);
        }
    }

    /**
     * Create content bytes of a specified size.
     */
    private byte[] createContentBytes(int size) {
        StringBuilder buffer = new StringBuilder(size);
        byte count = 0;
        for (int i = 0; i < size; i++) {
            buffer.append(count+"");
            count++;
            if (count > 9) {
                count = 0;
            }
        }
        return buffer.toString().getBytes();
    }

    /**
     * Create a FileItem with the specfied content bytes.
     */
    private FileItem createFileItem(byte[] contentBytes) {
        FileItemFactory factory = new DiskFileItemFactory(threshold, null);
        String textFieldName = "textField";

        FileItem item = factory.createItem(
                textFieldName,
                textContentType,
                true,
                "My File Name"
        );
        try {
            OutputStream os = item.getOutputStream();
            os.write(contentBytes);
            os.close();
        } catch(IOException e) {
            fail("Unexpected IOException" + e);
        }

        return item;

    }

    /**
     * Do serialization and deserialization.
     */
    private Object serializeDeserialize(Object target) {
        // Serialize the test object
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try {
            ObjectOutputStream oos = new ObjectOutputStream(baos);
            oos.writeObject(target);
            oos.flush();
            oos.close();
        } catch (Exception e) {
            fail("Exception during serialization: " + e);
        }

        // Deserialize the test object
        Object result = null;
        try {
            ByteArrayInputStream bais =
                new ByteArrayInputStream(baos.toByteArray());
            ObjectInputStream ois = new ObjectInputStream(bais);
            result = ois.readObject();
            bais.close();
        } catch (Exception e) {
            fail("Exception during deserialization: " + e);
        }
        return result;
    }

}
